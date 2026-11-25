//! Source-derived collision geometry from Flappy Madruga.caproj.

pub type Point = [f32; 2];

/// Madruga's default sprite collision polygon, normalized to [0, 1].
pub const MADRUGA_DEFAULT: [Point; 8] = [
    [0.727234, 0.207161],
    [0.857570, 0.241620],
    [0.945398, 0.287442],
    [0.954768, 0.477782],
    [0.887391, 1.000000],
    [0.584545, 0.922743],
    [0.355524, 0.656003],
    [0.434210, 0.326143],
];

/// Madruga's Flying animation collision polygon, normalized to [0, 1].
pub const MADRUGA_FLYING: [Point; 8] = [
    [0.470395, 0.282787],
    [0.723684, 0.172131],
    [0.953947, 0.262295],
    [0.957237, 0.467213],
    [0.881579, 1.000000],
    [0.562500, 0.913934],
    [0.358553, 0.688525],
    [0.365131, 0.405738],
];

/// TopPipe's default collision polygon.
pub const PIPE_DEFAULT: [Point; 6] = [
    [0.114286, 0.013245],
    [0.500000, 0.000000],
    [0.900000, 0.011589],
    [0.900000, 0.988411],
    [0.500000, 1.000000],
    [0.114286, 0.986755],
];

pub const TOP_PIPE_CHAVES: [[Point; 7]; 4] = [
    [
        [0.212766, 0.032949], [0.500000, 0.000000], [0.797872, 0.031302],
        [0.797872, 0.968699], [0.500000, 0.995058], [0.212766, 0.967051],
        [0.212766, 0.967051],
    ],
    [
        [0.212766, 0.032949], [0.500000, 0.000000], [0.797872, 0.031302],
        [0.797872, 0.968699], [0.500000, 0.995058], [0.042553, 0.993410],
        [0.212766, 0.499176],
    ],
    [
        [0.212766, 0.031302], [0.500000, 0.000000], [0.797872, 0.031302],
        [0.797872, 0.968699], [0.500000, 0.995058], [0.202128, 0.968699],
        [0.202128, 0.968699],
    ],
    [
        [0.212766, 0.032949], [0.500000, 0.000000], [0.797872, 0.031302],
        [0.797872, 0.968699], [0.500000, 0.995058], [0.212766, 0.967051],
        [0.212766, 0.967051],
    ],
];

pub const BOTTOM_PIPE_CHAVES: [[Point; 7]; 4] = [
    [
        [0.212766, 0.032949], [0.500000, 0.004942], [0.797872, 0.031302],
        [0.797872, 0.968699], [0.500000, 1.000000], [0.212766, 0.967051],
        [0.212766, 0.967051],
    ],
    [
        [0.042553, 0.006590], [0.500000, 0.004942], [0.797872, 0.031302],
        [0.797872, 0.968699], [0.500000, 1.000000], [0.212766, 0.967051],
        [0.212766, 0.499176],
    ],
    [
        [0.202128, 0.031302], [0.500000, 0.004942], [0.797872, 0.031302],
        [0.797872, 0.968699], [0.500000, 1.000000], [0.212766, 0.967051],
        [0.212766, 0.967051],
    ],
    [
        [0.212766, 0.032949], [0.500000, 0.004942], [0.797872, 0.031302],
        [0.797872, 0.968699], [0.500000, 1.000000], [0.212766, 0.967051],
        [0.212766, 0.967051],
    ],
];

/// Transform normalized Construct collision points through the object's
/// hotspot and rotation into world coordinates.
pub fn transform_polygon(
    points: &[Point],
    position: Point,
    size: Point,
    hotspot: Point,
    angle_degrees: f32,
) -> Vec<Point> {
    let angle = angle_degrees.to_radians();
    let (sin, cos) = angle.sin_cos();

    points
        .iter()
        .map(|point| {
            let local_x = (point[0] - hotspot[0]) * size[0];
            let local_y = (point[1] - hotspot[1]) * size[1];

            // Construct's screen-space positive angle rotates clockwise.
            [
                position[0] + local_x * cos - local_y * sin,
                position[1] + local_x * sin + local_y * cos,
            ]
        })
        .collect()
}

pub fn rectangle_polygon(x: f32, y: f32, width: f32, height: f32) -> Vec<Point> {
    vec![
        [x, y],
        [x + width, y],
        [x + width, y + height],
        [x, y + height],
    ]
}

fn project_polygon(points: &[Point], axis: Point) -> (f32, f32) {
    let mut min = f32::INFINITY;
    let mut max = f32::NEG_INFINITY;

    for point in points {
        let projection = point[0] * axis[0] + point[1] * axis[1];
        min = min.min(projection);
        max = max.max(projection);
    }

    (min, max)
}

fn has_separating_axis(source: &[Point], other: &[Point]) -> bool {
    for index in 0..source.len() {
        let a = source[index];
        let b = source[(index + 1) % source.len()];
        let edge = [b[0] - a[0], b[1] - a[1]];
        let axis = [-edge[1], edge[0]];

        if axis[0].abs() + axis[1].abs() < f32::EPSILON {
            continue;
        }

        let (a_min, a_max) = project_polygon(source, axis);
        let (b_min, b_max) = project_polygon(other, axis);

        if a_max < b_min || b_max < a_min {
            return true;
        }
    }

    false
}

/// Separating Axis Theorem for the convex polygons used by this project.
pub fn polygons_intersect(a: &[Point], b: &[Point]) -> bool {
    if a.len() < 3 || b.len() < 3 {
        return false;
    }

    !has_separating_axis(a, b) && !has_separating_axis(b, a)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rectangle_sat_detects_overlap_and_separation() {
        let a = rectangle_polygon(0.0, 0.0, 10.0, 10.0);
        let touching = rectangle_polygon(9.0, 9.0, 10.0, 10.0);
        let separate = rectangle_polygon(11.0, 0.0, 10.0, 10.0);

        assert!(polygons_intersect(&a, &touching));
        assert!(!polygons_intersect(&a, &separate));
    }

    #[test]
    fn source_sprite_polygon_is_transformed_around_its_hotspot() {
        let polygon = transform_polygon(
            &MADRUGA_DEFAULT,
            [69.332_04, 240.193_33],
            [73.076_92, 56.447_76],
            [0.513158, 0.524590],
            0.0,
        );

        assert_eq!(polygon.len(), 8);
        assert!(polygon.iter().all(|point| point[0].is_finite() && point[1].is_finite()));
    }
}
