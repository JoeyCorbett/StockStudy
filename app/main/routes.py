from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.main import main_bp
from app.models.study_group import StudyGroup
from app.extensions import db

@main_bp.route('/')
@login_required
def index():
    study_groups = StudyGroup.query.all()

    return render_template('index.html', study_groups=study_groups)

@main_bp.route("/create-group", methods=['POST'])
@login_required
def create_group():
    group_name = request.form.get("group-name")
    subject = request.form.get("subject")
    description = request.form.get("description")
    location = request.form.get("location")
    max_members = request.form.get("max-members")

    if not group_name or not subject or not description or not location or not max_members:
        flash("All fields are required!", "danger")
        return redirect(url_for('main.index'))
    
    try:
        new_group = StudyGroup(
            name = group_name,
            subject = subject,
            description = description,
            location = location,
            max_members = int(max_members),
            owner=current_user
        )

        # Add current user as member
        new_group.members.append(current_user)

        db.session.add(new_group)
        db.session.commit()

        flash("Group created successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error has occured: {str(e)}", "error")
    
    return redirect(url_for('main.index'))
    

