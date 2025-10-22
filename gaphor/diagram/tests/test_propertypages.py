from gaphor.core.modeling import Diagram
from gaphor.diagram.general import Line
from gaphor.diagram.propertypages import (
    InternalsPropertyPage,
    LineStylePage,
    NamePropertyPage,
    NotePropertyPage,
)
from gaphor.diagram.tests.fixtures import find
from gaphor.UML import Comment
from gaphor.UML.general import CommentItem


def test_name_page(element_factory, event_manager):
    diagram = element_factory.create(Diagram)
    property_page = NamePropertyPage(diagram, event_manager)
    widget = property_page.construct()
    name = find(widget, "name-entry")
    name.set_text("A new note")

    assert diagram.name == "A new note"


def test_line_style_page_rectilinear(diagram, event_manager):
    item = diagram.create(Line)
    property_page = LineStylePage(item, event_manager)
    widget = property_page.construct()
    line_rectangular = find(widget, "line-rectilinear")

    line_rectangular.set_active(True)

    assert item.orthogonal


def test_line_style_page_orientation(diagram, event_manager):
    item = diagram.create(Line)
    property_page = LineStylePage(item, event_manager)
    widget = property_page.construct()
    flip_orientation = find(widget, "flip-orientation")
    flip_orientation.set_active(True)

    assert item.horizontal


def test_note_page_with_item_without_subject(diagram, event_manager):
    item = diagram.create(Line)
    property_page = NotePropertyPage(item, event_manager)
    widget = property_page.construct()

    assert not widget


def test_note_page_with_item_with_subject(create, event_manager):
    item = create(CommentItem, Comment)
    property_page = NotePropertyPage(item, event_manager)
    widget = property_page.construct()

    note = find(widget, "note")
    note.get_buffer().set_text("A new note")

    assert item.subject.note == "A new note"


def test_note_page_with_subject(element_factory, event_manager):
    comment = element_factory.create(Comment)
    property_page = NotePropertyPage(comment, event_manager)
    widget = property_page.construct()

    note = find(widget, "note")
    note.get_buffer().set_text("A new note")

    assert comment.note == "A new note"


def test_internals_page_for_presentation(create):
    subject = create(CommentItem, Comment)
    property_page = InternalsPropertyPage(subject)
    widget = property_page.construct()

    internals = find(widget, "internals")
    text = internals.get_label()

    assert "CommentItem" in text
    assert "gaphor.UML.Comment" in text
