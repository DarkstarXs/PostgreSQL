import flask
import models
import forms

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)

@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )

@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))

@app.route("/notes/delete/<int:note_id>", methods=["POST"])
def notes_delete(note_id):
    db = models.db
    note = db.session.execute(db.select(models.Note).where(models.Note.id == note_id)).scalars().first()

    if note:
        db.session.delete(note)
        db.session.commit()

    return flask.redirect(flask.url_for("index"))

@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )

@app.route("/notes/edit/<int:note_id>", methods=["GET", "POST"])
def notes_edit(note_id):
    note = models.Note.query.get(note_id)
    
    if not note:
        return flask.redirect(flask.url_for("index"))

    form = forms.NoteForm()
    
    if not form.validate_on_submit():
 
        form.title.data =note.title
        form.description.data =note.description
        form.tags.data = ",".join([i.name for i in note.tags])

        # flash('Note updated successfully', 'success')
        return flask.render_template("notes-edit.html", form=form, note_id=note_id)
    note.title = form.title.data
    note.description = form.description.data

    db = models.db
    note.tags = []
    for tag_name in form.tags.data:
        tag = db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name)).scalars().first()

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)


    models.db.session.commit()
    
    return flask.redirect(flask.url_for('index'))

@app.route("/tags/delete/<tag_name>", methods=["POST"])
def tags_delete(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )

    if tag:
        # Remove tag association from notes
        notes = db.session.execute(
            db.select(models.Note).where(models.Note.tags.any(id=tag.id))
        ).scalars().all()

        for note in notes:
            note.tags.remove(tag)

        # Now delete the tag itself
        db.session.delete(tag)
        db.session.commit()

    return flask.redirect(flask.url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
