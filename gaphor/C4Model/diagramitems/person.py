from math import pi

from gaphor.C4Model import c4model
from gaphor.diagram.presentation import ElementPresentation, Named, text_name
from gaphor.diagram.shapes import Box, CssNode, Text, stroke
from gaphor.diagram.support import represents


@represents(c4model.Person)
class C4PersonItem(Named, ElementPresentation):
    def __init__(self, diagram, id=None):
        super().__init__(diagram, id, width=48, height=48)

        self.watch("subject[UML:NamedElement].name")
        self.watch("subject[Person].description")

    def update_shapes(self, event=None):
        self.shape = Box(
            text_name(self),
            CssNode(
                "technology",
                self.subject,
                Text(
                    text=lambda: f"[{self.diagram.gettext('Person')}]",
                ),
            ),
            CssNode(
                "description",
                self.subject,
                Text(
                    text=lambda: self.subject.description or "",
                ),
            ),
            draw=draw_person,
        )


def draw_person(box, context, bounding_box):
    cr = context.cairo
    d = context.style.get("border-radius", 24)
    x, y, width, height = bounding_box

    x1 = width + x
    y1 = height + y
    d_head = width * 0.19
    cr.move_to(x, d)
    cr.arc(d, d, d, pi, 1.5 * pi)
    cr.line_to(x + width / 2 - d_head / 2, y)
    cr.arc(x + width / 2, -d_head * 0.866, d_head, 2 / 3 * pi, 1 / 3 * pi)
    cr.line_to(x1 - d, y)
    cr.arc(x1 - d, d, d, 1.5 * pi, y)
    cr.line_to(x1, y1 - d)
    cr.arc(x1 - d, y1 - d, d, 0, 0.5 * pi)
    cr.line_to(d, y1)
    cr.arc(d, y1 - d, d, 0.5 * pi, pi)

    cr.close_path()

    stroke(context, fill=True)
