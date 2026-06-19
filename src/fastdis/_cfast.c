#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <string.h>

typedef struct {
    unsigned int version;
    unsigned int exercise_id;
    unsigned int pdu_type;
    unsigned int protocol_family;
    uint32_t timestamp;
    uint16_t length;
    int status;          /* -1 for DIS <= 6 / pre-status headers */
    unsigned int padding;/* DIS7: one byte. DIS6: two bytes. */
} dis_header;

static uint16_t be16(const unsigned char *p) {
    return (uint16_t)(((uint16_t)p[0] << 8) | (uint16_t)p[1]);
}

static uint32_t be32(const unsigned char *p) {
    return ((uint32_t)p[0] << 24) |
           ((uint32_t)p[1] << 16) |
           ((uint32_t)p[2] << 8)  |
           ((uint32_t)p[3]);
}

static int invalid_packet(int strict, const char *message) {
    if (strict) {
        PyErr_SetString(PyExc_ValueError, message);
        return -1;
    }
    return 0;
}

/*
 * Return values:
 *   1 = valid header parsed
 *   0 = invalid/rejected packet and strict == 0
 *  -1 = Python exception set
 */
static int parse_dis_header(const unsigned char *buf, Py_ssize_t n, int strict, dis_header *out) {
    if (n < 12) {
        return invalid_packet(strict, "DIS PDU is shorter than the 12-byte header");
    }

    out->version = (unsigned int)buf[0];
    out->exercise_id = (unsigned int)buf[1];
    out->pdu_type = (unsigned int)buf[2];
    out->protocol_family = (unsigned int)buf[3];
    out->timestamp = be32(buf + 4);
    out->length = be16(buf + 8);

    if (out->length < 12) {
        return invalid_packet(strict, "DIS PDU length field is smaller than the header");
    }
    if ((Py_ssize_t)out->length > n) {
        return invalid_packet(strict, "DIS PDU length field exceeds supplied buffer length");
    }

    if (out->version >= 7) {
        out->status = (int)buf[10];
        out->padding = (unsigned int)buf[11];
    } else {
        out->status = -1;
        out->padding = (unsigned int)be16(buf + 10);
    }

    return 1;
}

static int fill_mask(PyObject *obj, unsigned char mask[256], int *active, const char *name) {
    memset(mask, 0, 256);
    *active = 0;

    if (obj == NULL || obj == Py_None) {
        return 1;
    }

    *active = 1;

    if (PyLong_Check(obj)) {
        long v = PyLong_AsLong(obj);
        if (v == -1 && PyErr_Occurred()) {
            return 0;
        }
        if (v < 0 || v > 255) {
            PyErr_Format(PyExc_ValueError, "%s values must be in the range 0..255", name);
            return 0;
        }
        mask[(unsigned char)v] = 1;
        return 1;
    }

    PyObject *iter = PyObject_GetIter(obj);
    if (iter == NULL) {
        PyErr_Format(PyExc_TypeError, "%s must be None, an int, or an iterable of ints", name);
        return 0;
    }

    PyObject *item;
    while ((item = PyIter_Next(iter)) != NULL) {
        long v = PyLong_AsLong(item);
        Py_DECREF(item);
        if (v == -1 && PyErr_Occurred()) {
            Py_DECREF(iter);
            return 0;
        }
        if (v < 0 || v > 255) {
            Py_DECREF(iter);
            PyErr_Format(PyExc_ValueError, "%s values must be in the range 0..255", name);
            return 0;
        }
        mask[(unsigned char)v] = 1;
    }

    Py_DECREF(iter);
    if (PyErr_Occurred()) {
        return 0;
    }
    return 1;
}

typedef struct {
    unsigned char pdu_types[256];
    unsigned char versions[256];
    unsigned char families[256];
    unsigned char exercise_ids[256];
    int has_pdu_types;
    int has_versions;
    int has_families;
    int has_exercise_ids;
} filters;

static int build_filters(filters *f,
                         PyObject *pdu_types,
                         PyObject *versions,
                         PyObject *families,
                         PyObject *exercise_ids) {
    if (!fill_mask(pdu_types, f->pdu_types, &f->has_pdu_types, "pdu_types")) {
        return 0;
    }
    if (!fill_mask(versions, f->versions, &f->has_versions, "versions")) {
        return 0;
    }
    if (!fill_mask(families, f->families, &f->has_families, "families")) {
        return 0;
    }
    if (!fill_mask(exercise_ids, f->exercise_ids, &f->has_exercise_ids, "exercise_ids")) {
        return 0;
    }
    return 1;
}

static int matches_filters(const filters *f, const dis_header *h) {
    if (f->has_pdu_types && !f->pdu_types[h->pdu_type]) {
        return 0;
    }
    if (f->has_versions && !f->versions[h->version]) {
        return 0;
    }
    if (f->has_families && !f->families[h->protocol_family]) {
        return 0;
    }
    if (f->has_exercise_ids && !f->exercise_ids[h->exercise_id]) {
        return 0;
    }
    return 1;
}

static PyObject *header_tuple(const dis_header *h) {
    PyObject *t = PyTuple_New(8);
    if (t == NULL) {
        return NULL;
    }

    PyObject *items[8];
    items[0] = PyLong_FromUnsignedLong(h->version);
    items[1] = PyLong_FromUnsignedLong(h->exercise_id);
    items[2] = PyLong_FromUnsignedLong(h->pdu_type);
    items[3] = PyLong_FromUnsignedLong(h->protocol_family);
    items[4] = PyLong_FromUnsignedLong((unsigned long)h->timestamp);
    items[5] = PyLong_FromUnsignedLong((unsigned long)h->length);
    items[6] = PyLong_FromLong((long)h->status);
    items[7] = PyLong_FromUnsignedLong(h->padding);

    for (int i = 0; i < 8; i++) {
        if (items[i] == NULL) {
            for (int j = 0; j < 8; j++) {
                Py_XDECREF(items[j]);
            }
            Py_DECREF(t);
            return NULL;
        }
    }

    for (int i = 0; i < 8; i++) {
        if (PyTuple_SetItem(t, i, items[i]) < 0) {
            for (int j = i; j < 8; j++) {
                Py_DECREF(items[j]);
            }
            Py_DECREF(t);
            return NULL;
        }
    }
    return t;
}

static PyObject *parse_header_py(PyObject *self, PyObject *args, PyObject *kwargs) {
    (void)self;
    PyObject *obj;
    int strict = 1;
    static char *kwlist[] = {"data", "strict", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|p:parse_header", kwlist, &obj, &strict)) {
        return NULL;
    }

    Py_buffer view;
    if (PyObject_GetBuffer(obj, &view, PyBUF_SIMPLE) < 0) {
        return NULL;
    }

    dis_header h;
    int ok = parse_dis_header((const unsigned char *)view.buf, view.len, strict, &h);
    PyBuffer_Release(&view);

    if (ok < 0) {
        return NULL;
    }
    if (ok == 0) {
        Py_RETURN_NONE;
    }
    return header_tuple(&h);
}

static PyObject *call_packet_callback(PyObject *callback, const dis_header *h, PyObject *packet) {
    PyObject *cb_args = PyTuple_New(8);
    if (cb_args == NULL) {
        return NULL;
    }

    PyObject *items[8];
    items[0] = PyLong_FromUnsignedLong(h->version);
    items[1] = PyLong_FromUnsignedLong(h->exercise_id);
    items[2] = PyLong_FromUnsignedLong(h->pdu_type);
    items[3] = PyLong_FromUnsignedLong(h->protocol_family);
    items[4] = PyLong_FromUnsignedLong((unsigned long)h->timestamp);
    items[5] = PyLong_FromUnsignedLong((unsigned long)h->length);
    items[6] = PyLong_FromLong((long)h->status);
    Py_INCREF(packet);
    items[7] = packet;

    for (int i = 0; i < 8; i++) {
        if (items[i] == NULL) {
            for (int j = 0; j < 8; j++) {
                Py_XDECREF(items[j]);
            }
            Py_DECREF(cb_args);
            return NULL;
        }
    }

    for (int i = 0; i < 8; i++) {
        if (PyTuple_SetItem(cb_args, i, items[i]) < 0) {
            for (int j = i; j < 8; j++) {
                Py_DECREF(items[j]);
            }
            Py_DECREF(cb_args);
            return NULL;
        }
    }

    PyObject *result = PyObject_CallObject(callback, cb_args);
    Py_DECREF(cb_args);
    return result;
}

static PyObject *scan_many_py(PyObject *self, PyObject *args, PyObject *kwargs) {
    (void)self;
    PyObject *packets;
    PyObject *callback;
    PyObject *pdu_types = Py_None;
    PyObject *versions = Py_None;
    PyObject *families = Py_None;
    PyObject *exercise_ids = Py_None;
    Py_ssize_t sample_every = 1;
    Py_ssize_t sample_offset = 0;
    int strict = 0;
    static char *kwlist[] = {
        "packets", "callback", "pdu_types", "versions", "families", "exercise_ids",
        "sample_every", "sample_offset", "strict", NULL
    };

    if (!PyArg_ParseTupleAndKeywords(
            args, kwargs, "OO|OOOOnnp:scan_many", kwlist,
            &packets, &callback, &pdu_types, &versions, &families, &exercise_ids,
            &sample_every, &sample_offset, &strict)) {
        return NULL;
    }

    if (callback != Py_None && !PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "callback must be callable or None");
        return NULL;
    }
    if (sample_every < 1) {
        PyErr_SetString(PyExc_ValueError, "sample_every must be >= 1");
        return NULL;
    }
    Py_ssize_t normalized_offset = sample_offset % sample_every;
    if (normalized_offset < 0) {
        normalized_offset += sample_every;
    }

    filters f;
    if (!build_filters(&f, pdu_types, versions, families, exercise_ids)) {
        return NULL;
    }

    PyObject *iter = PyObject_GetIter(packets);
    if (iter == NULL) {
        return NULL;
    }

    unsigned long long seen = 0;
    unsigned long long accepted = 0;
    unsigned long long emitted = 0;

    PyObject *packet;
    while ((packet = PyIter_Next(iter)) != NULL) {
        seen++;
        Py_buffer view;
        if (PyObject_GetBuffer(packet, &view, PyBUF_SIMPLE) < 0) {
            if (strict) {
                Py_DECREF(packet);
                Py_DECREF(iter);
                return NULL;
            }
            PyErr_Clear();
            Py_DECREF(packet);
            continue;
        }

        dis_header h;
        int ok = parse_dis_header((const unsigned char *)view.buf, view.len, strict, &h);
        PyBuffer_Release(&view);

        if (ok < 0) {
            Py_DECREF(packet);
            Py_DECREF(iter);
            return NULL;
        }

        if (ok == 1 && matches_filters(&f, &h)) {
            unsigned long long accepted_index = accepted;
            accepted++;
            if ((Py_ssize_t)(accepted_index % (unsigned long long)sample_every) == normalized_offset) {
                emitted++;
                if (callback != Py_None) {
                    PyObject *result = call_packet_callback(callback, &h, packet);
                    if (result == NULL) {
                        Py_DECREF(packet);
                        Py_DECREF(iter);
                        return NULL;
                    }
                    Py_DECREF(result);
                }
            }
        }

        Py_DECREF(packet);
    }

    Py_DECREF(iter);
    if (PyErr_Occurred()) {
        return NULL;
    }

    return Py_BuildValue("(KKK)", seen, accepted, emitted);
}

static PyObject *count_by_type_py(PyObject *self, PyObject *args, PyObject *kwargs) {
    (void)self;
    PyObject *packets;
    PyObject *versions = Py_None;
    PyObject *families = Py_None;
    PyObject *exercise_ids = Py_None;
    int strict = 0;
    static char *kwlist[] = {"packets", "versions", "families", "exercise_ids", "strict", NULL};

    if (!PyArg_ParseTupleAndKeywords(
            args, kwargs, "O|OOOp:count_by_type", kwlist,
            &packets, &versions, &families, &exercise_ids, &strict)) {
        return NULL;
    }

    filters f;
    if (!build_filters(&f, Py_None, versions, families, exercise_ids)) {
        return NULL;
    }

    unsigned long long counts[256];
    memset(counts, 0, sizeof(counts));

    PyObject *iter = PyObject_GetIter(packets);
    if (iter == NULL) {
        return NULL;
    }

    PyObject *packet;
    while ((packet = PyIter_Next(iter)) != NULL) {
        Py_buffer view;
        if (PyObject_GetBuffer(packet, &view, PyBUF_SIMPLE) < 0) {
            if (strict) {
                Py_DECREF(packet);
                Py_DECREF(iter);
                return NULL;
            }
            PyErr_Clear();
            Py_DECREF(packet);
            continue;
        }

        dis_header h;
        int ok = parse_dis_header((const unsigned char *)view.buf, view.len, strict, &h);
        PyBuffer_Release(&view);

        if (ok < 0) {
            Py_DECREF(packet);
            Py_DECREF(iter);
            return NULL;
        }
        if (ok == 1 && matches_filters(&f, &h)) {
            counts[h.pdu_type]++;
        }
        Py_DECREF(packet);
    }

    Py_DECREF(iter);
    if (PyErr_Occurred()) {
        return NULL;
    }

    PyObject *list = PyList_New(256);
    if (list == NULL) {
        return NULL;
    }
    for (int i = 0; i < 256; i++) {
        PyObject *v = PyLong_FromUnsignedLongLong(counts[i]);
        if (v == NULL || PyList_SetItem(list, i, v) < 0) {
            Py_XDECREF(v);
            Py_DECREF(list);
            return NULL;
        }
    }
    return list;
}

static PyMethodDef FastDisMethods[] = {
    {"parse_header", (PyCFunction)parse_header_py, METH_VARARGS | METH_KEYWORDS,
     "parse_header(data, strict=True) -> tuple | None\n\nParse a 12-byte DIS PDU header without creating PDU objects."},
    {"scan_many", (PyCFunction)scan_many_py, METH_VARARGS | METH_KEYWORDS,
     "scan_many(packets, callback, *, pdu_types=None, versions=None, families=None, exercise_ids=None, sample_every=1, sample_offset=0, strict=False) -> (seen, accepted, emitted)"},
    {"count_by_type", (PyCFunction)count_by_type_py, METH_VARARGS | METH_KEYWORDS,
     "count_by_type(packets, *, versions=None, families=None, exercise_ids=None, strict=False) -> list[int]"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef fastdis_module = {
    PyModuleDef_HEAD_INIT,
    "_cfast",
    "Optional C accelerator for fastdis.",
    -1,
    FastDisMethods
};

PyMODINIT_FUNC PyInit__cfast(void) {
    return PyModule_Create(&fastdis_module);
}
