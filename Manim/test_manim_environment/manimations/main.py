from manim import *
import numpy as np

def calculateDistanceFocuspoint(semi_major_axes, semi_minor_axes) -> float:
    return np.sqrt(semi_major_axes**2 - semi_minor_axes**2)

class TestScene(Scene):
    def construct(self):
        # Ellipse parameters
        a = 3       # semi-major
        b = 1.5     # semi-minor
        ellipse = Ellipse(width=2*a, height=2*b, color=WHITE)
        ellipseGraph = ParametricFunction(
            lambda t: np.array([
                a * np.cos(t),
                b * np.sin(t),
                0
            ]),
            t_range=[0, TAU],
            color=GREEN,
            stroke_width=4
        )
        
        # Foci
        c = calculateDistanceFocuspoint(a, b)
        focus1_pos = LEFT * c
        focus2_pos = RIGHT * c
        focus1 = Dot(focus1_pos, color=RED)
        focus2 = Dot(focus2_pos, color=RED)
        
        # Major and minor axes
        semi_major_axes = Line(LEFT*a, RIGHT*a, color=BLUE)
        semi_minor_axes = Line(UP*b, DOWN*b, color=BLUE)
        
        # Lines from center to foci (optional)
        distance_a_1 = Line(ORIGIN, focus1_pos, color=YELLOW)
        distance_a_2 = Line(ORIGIN, focus2_pos, color=YELLOW)
        
        # Points along the ellipse (using proportion along the outline)
        num_points = 50
        points_on_ellipse = [ellipse.point_from_proportion(i/num_points) for i in range(num_points)]
        
        # Lines from each point on the ellipse to both foci
        focus_lines = []
        for p in points_on_ellipse:
            focus_lines.append(Line(p, focus1_pos, color=GREEN, stroke_width = 0.5))
            focus_lines.append(Line(p, focus2_pos, color=ORANGE, stroke_width = 0.5))
        
        # Add everything to the scene
        self.play(Create(ellipse))
        self.add(semi_major_axes, semi_minor_axes, distance_a_1, distance_a_2)
        self.play(Create(focus1), Create(focus2))

        # create lines from focuspoints
        for line in focus_lines:
            self.play(Create(line), run_time=0.1, rate_func=linear)
        
        self.wait(2)

        self.add(ellipseGraph)

        theta = ValueTracker(0)

        dot = always_redraw(
            lambda: Dot(
                np.array([
                    a*np.cos(theta.get_value()),
                    b*np.sin(theta.get_value()),
                    0
                ]),
                color=YELLOW
            )
        )

        self.add(dot)
        self.play(theta.animate.set_value(TAU), run_time=4, rate_func=linear)
        self.wait()

