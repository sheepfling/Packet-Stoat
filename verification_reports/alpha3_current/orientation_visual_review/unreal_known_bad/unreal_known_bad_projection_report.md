# Orientation Visual Projection Report

- generated_at: `2026-06-19T20:26:44.234785+00:00`
- engine: `unreal`
- label: `known_bad`
- config_hash: `sha256:33dcbdaf79477a22fd944e87b15f153d7a9c07cf8befbf37b0a082a84901d943`

| case | camera | projection_err_px | screen_angle_deg | image_mae | signature | pass |
| --- | --- | ---: | ---: | ---: | --- | --- |
| level_north | top_down | 155.563 | 90.000 | 0.854 | determinant_negative | FAIL |
| level_north | side_east | 110.000 | 115.577 | 0.569 | determinant_negative | FAIL |
| level_north | perspective | 155.563 | 120.000 | 0.738 | determinant_negative | FAIL |
| level_east | top_down | 155.563 | 90.000 | 1.163 | determinant_negative | FAIL |
| level_east | side_east | 110.000 | 126.384 | 0.726 | determinant_negative | FAIL |
| level_east | perspective | 155.563 | 120.000 | 0.988 | determinant_negative | FAIL |
| level_south | top_down | 155.563 | 90.000 | 0.854 | determinant_negative | FAIL |
| level_south | side_east | 110.000 | 90.000 | 0.569 | determinant_negative | FAIL |
| level_south | perspective | 155.563 | 120.000 | 0.732 | determinant_negative | FAIL |
| level_west | top_down | 155.563 | 90.000 | 1.163 | determinant_negative | FAIL |
| level_west | side_east | 110.000 | 33.690 | 0.726 | determinant_negative | FAIL |
| level_west | perspective | 155.563 | 120.000 | 0.993 | determinant_negative | FAIL |
| climb_north_20deg | top_down | 155.563 | 90.000 | 1.024 | determinant_negative | FAIL |
| climb_north_20deg | side_east | 110.000 | 70.000 | 1.219 | determinant_negative | FAIL |
| climb_north_20deg | perspective | 155.563 | 120.000 | 1.321 | determinant_negative | FAIL |
| bank_right_30deg | top_down | 155.563 | 90.000 | 0.884 | determinant_negative | FAIL |
| bank_right_30deg | side_east | 110.000 | 115.577 | 1.370 | determinant_negative | FAIL |
| bank_right_30deg | perspective | 155.563 | 169.792 | 1.440 | determinant_negative | FAIL |
| adelaide_heading_135_pitch_20_roll_30 | top_down | 206.732 | 180.000 | 1.255 | determinant_negative | FAIL |
| adelaide_heading_135_pitch_20_roll_30 | side_east | 146.182 | 125.527 | 1.378 | determinant_negative | FAIL |
| adelaide_heading_135_pitch_20_roll_30 | perspective | 206.732 | 146.898 | 1.336 | determinant_negative | FAIL |
| equator_prime_meridian_level_north | top_down | 155.563 | 90.000 | 0.854 | determinant_negative | FAIL |
| equator_prime_meridian_level_north | side_east | 110.000 | 90.000 | 0.569 | determinant_negative | FAIL |
| equator_prime_meridian_level_north | perspective | 155.563 | 120.000 | 0.738 | determinant_negative | FAIL |
| near_pole_level_north | top_down | 155.563 | 90.000 | 0.854 | determinant_negative | FAIL |
| near_pole_level_north | side_east | 110.000 | 7.321 | 0.569 | determinant_negative | FAIL |
| near_pole_level_north | perspective | 155.563 | 120.000 | 0.738 | determinant_negative | FAIL |
