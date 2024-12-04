import os
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.main import main_bp
from app.models.study_group import StudyGroup
from app.extensions import db
import requests

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

@main_bp.route('/')
def landing():
    return render_template('landing.html')

@main_bp.route('/map-data')
def map_data():
    response = requests.get(
         f"https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_API_KEY}&libraries=maps,marker&v=beta"
    )
    return response.text

@main_bp.route('/my-groups')
@login_required
def my_groups():
    user_groups = current_user.study_groups

    return render_template('my-groups.html', study_groups=user_groups, user=current_user.id)

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
        return redirect(url_for('main.my_groups'))
    
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
    
    return redirect(url_for('main.my_groups'))

@main_bp.route("/find-groups")
@login_required
def find_groups():
    all_groups = StudyGroup.query.all()

    # Filter out joined groups and user-owned groups
    filtered_groups = []
    for group in all_groups:
        if current_user not in group.members and group.owner_id != current_user.id:
            filtered_groups.append(group)

    subjects = []
    for group in filtered_groups:
        subjects.append(group.subject)
    
    return render_template('find-groups.html', study_groups=filtered_groups, subjects=subjects)

@main_bp.route("/profile")
@login_required
def profile():
    user = current_user
    return render_template('profile.html', user=user)

@main_bp.route("/map")
@login_required
def map():
    return render_template('map.html')

@main_bp.route("/join-group", methods=['POST'])
@login_required
def join_group():
    group_id = request.form.get("group_id")

    if not group_id:
        flash("Invalid Group ID", "danger")
        return redirect(url_for('main.my_groups'))
    
    # check if group exists
    group = StudyGroup.query.filter_by(id=group_id).first()
    if not group:
        flash("Study group not found!", "danger")
        return redirect(url_for('main.my_groups'))
    
    if current_user in group.members:
        flash("You are already a member of this group!", "info")
        return redirect(url_for('main.my_groups'))

    try:
        group.members.append(current_user)
        group.current_members += 1
        db.session.commit()
        flash(f"You have joined {group.name}!", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occured: {str(e)}", "danger")
    
    return redirect(url_for('main.find_groups'))

@main_bp.route("/group/<group_id>", methods=['GET'])
@login_required
def view_group(group_id):
    if not group_id:
        flash("Invalid Group ID", "danger")
        return redirect(url_for('main.my_groups'))
    
    # check if group exists
    group = StudyGroup.query.filter_by(id=group_id).first()
    if not group:
        flash("Study group not found!", "danger")
        return redirect(url_for('main.my_groups'))
    
    # Check if user is a part of group
    if current_user not in group.members:
        flash("You are not a member of this group.", "danger")
        return redirect(url_for('main.my_groups'))
     
    return render_template("view-group.html", group=group, members=group.members, user=current_user, group_id=group_id)

@main_bp.route("/manage-group/<group_id>", methods=['GET'])
@login_required
def manage_group(group_id):
    if not group_id:
        flash("Invalid Group ID", "danger")
        return redirect(url_for('main.my_groups'))
    
    # check if group exists
    group = StudyGroup.query.filter_by(id=group_id).first()
    if not group:
        flash("Study group not found!", "danger")
        return redirect(url_for('main.my_groups'))
    
    # Check if user is owner of group
    if group.owner_id != current_user.id:
        flash("You are not the owner of this group.", "danger")
        return redirect(url_for('main.my_groups'))
     
    return render_template("manage-group.html", group=group, members=group.members, user=current_user, group_id=group_id)
    

@main_bp.route("/leave-group/<group_id>", methods=['POST'])
@login_required
def leave_group(group_id):
    if not group_id:
        flash("Invalid Group ID", "danger")
        return redirect(url_for('main.my_groups'))
    
    # check if group exists
    group = StudyGroup.query.filter_by(id=group_id).first()
    if not group:
        flash("Study group not found!", "danger")
        return redirect(url_for('main.my_groups'))
    
    if current_user not in group.members:
        flash("You are not a member of this group.", "info")
        return redirect(url_for('main.my_groups'))
    
    try:
        group.members.remove(current_user)
        group.current_members -= 1
        db.session.commit()
        flash(f"You have left {group.name}.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occured: {str(e)}", "danger")

    return redirect(url_for("main.my_groups"))
    
@main_bp.route("/delete-group/<group_id>", methods=['POST'])
@login_required
def delete_group(group_id):
    group = StudyGroup.query.get(group_id)
    if current_user.id != group.owner_id:
        flash("You do not have permission to delete this group", "danger")
        return redirect(url_for('main.my_groups'))
    
    group.members.clear()
    db.session.delete(group)
    db.session.commit()

    flash(f"Study group '{group.name}' deleted successfully", "success")
    return redirect(url_for('main.my_groups'))




