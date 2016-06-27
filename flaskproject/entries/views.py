from flask import Blueprint, render_template
from flask import request, redirect, url_for, json, current_app
from ..core import db
from flask_security import login_required, current_user
from .forms import CreateEntryForm, UpdateEntryForm
from flaskproject.cache import cache
from .models import Entry
from sqlalchemy import exc

entries = Blueprint('entries', __name__, template_folder='templates')

@entries.route('/')
@login_required
def index():
    entries = [entry for entry in Entry.query.all()]
    current_app.logger.info('Displaying all entries.')

    return render_template('entries/entries.html', entries=entries)

@entries.route('/')
@login_required
@cache.cached(300)
def display_entries():
    entries = [entry for entry in Entry.query.all()]
    current_app.logger.info('Displaying all entries.')

    return render_template("entries/entries.html", entries=entries)

@entries.route('/<entry_id>', methods=['GET', 'POST'])
@login_required
@cache.cached(300)
def show(entry_id):
    entry = Entry.query.filter_by(id=entry_id).first_or_404()

    return render_template("entries/show.html", entry=entry)

@entries.route('/edit/<entry_id>', methods=['GET', 'POST'])
@login_required
def update(entry_id):
    entry = Entry.query.filter_by(id=entry_id).first_or_404()

    user_id = current_user.id
    form = UpdateEntryForm()
    if request.method == "POST" and form.validate_on_submit():
        entry.title = form.title.data
        entry.body = form.body.data
        entry.user_id = user_id
        current_app.logger.info('Updating entry %s.', entry.title)
        # entry = Entry(title, body, user_id)

        try:
            # db.session.add(entry)
            db.session.commit()
            # return update(entry)
        except exc.SQLAlchemyError as e:
            current_app.logger.error(e)

            # return redirect(url_for('entries.show', entry_id=entry.id))
        return redirect(url_for('entries.display_entries'))
    else:
        form.title.data = entry.title
        form.body.data = entry.body

    return render_template("entries/edit.html", entry=entry, form=form)

@entries.route('/delete/<entry_id>', methods=['GET', 'POST'])
@login_required
def delete(entry_id):
    entry = Entry.query.filter_by(id=entry_id).first_or_404()
    user_id = current_user.id
    if user_id == entry.user_id:
        current_app.logger.info('Deleting entry %s.', entry.title)
        try:
            db.session.delete(entry)
            db.session.commit()
        except exc.SQLAlchemyError as e:
            current_app.logger.error(e)

        return redirect(url_for('entries.display_entries'))

    # db.session.delete(entry)
    # db.session.commit()

    return redirect(url_for('entries.display_entries'))


@entries.route('/create', methods=['GET', 'POST'])
@login_required
def create_entry():
    form = CreateEntryForm(request.form)
    user_id = current_user.id

    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        user_id = user_id
        current_app.logger.info('Adding a new entry %s.', (title))
        entry = Entry(title, body, user_id)

        try:
            db.session.add(entry)
            db.session.commit()
            cache.clear()
        except exc.SQLAlchemyError as e:
            current_app.logger.error(e)

            return redirect(url_for('entries'))

        return redirect(url_for('entries.display_entries'))

    return render_template("entries/create_entry.html", form=form)

