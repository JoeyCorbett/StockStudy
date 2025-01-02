import os
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.main import main_bp
from app.models.user import User
from app.models.study_group import StudyGroup
from app.models.membership_requests import GroupJoinRequest
from app.main.utils import get_request
from app.extensions import db
import requests
from sqlalchemy import or_
from sqlalchemy.orm import aliased
from app.utils import is_valid_password

MAPBOX_ACCESS_KEY = os.getenv('MAPBOX_ACCESS_KEY')

@main_bp.route('/')
def landing():
    return render_template('landing.html')

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
    group_type = request.form.get("group-type")

    if not group_name or not subject or not description or not group_type:
        flash("All fields are required!", "danger")
        return redirect(url_for('main.my_groups'))
    
    try:
        new_group = StudyGroup(
            name = group_name,
            subject = subject,
            description = description,
            group_type = group_type,
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

@main_bp.route('/inbox')
@login_required
def inbox():
    # get all requests for groups user owns
    group_requests = GroupJoinRequest.query.filter(
        GroupJoinRequest.group_id.in_(
            StudyGroup.query.with_entities(StudyGroup.id).filter_by(owner_id=current_user.id)
        ),
        GroupJoinRequest.status == 'pending'
    ).all()

    # get all pending requests for user
    user_requests = GroupJoinRequest.query.filter_by(user_id=current_user.id, status='pending').all()

    return render_template('inbox.html', group_requests=group_requests, user_requests=user_requests)

@main_bp.route('/accept-request/<int:request_id>/<int:group_id>', methods=['POST'])
@login_required
def accept_request(request_id, group_id):
    # make sure request exists / is valid
    group_request = get_request(request_id, group_id)
    if group_request is None:
        flash("Unauthorized or invalid request", "danger")
        return redirect(url_for('main.inbox'))

    # verify current user is owner of group 
    group = StudyGroup.query.get(group_request.group_id)
    if current_user.id != group.owner_id:
        flash("You are not the owner of this group", "danger")
        return redirect(url_for('main.inbox'))
    
    # Query user requesting to join
    user = User.query.get(group_request.user_id)

    GroupJoinRequest.approve(group_request)
    group.members.append(user)
    group.current_members += 1
    db.session.commit()

    flash(f"You have accepted {user.name}'s request to join {group.name}!", "info")
    return redirect(url_for('main.inbox'))

@main_bp.route('/reject-request/<int:request_id>/<int:group_id>', methods=['POST'])
@login_required
def reject_request(request_id, group_id):
    # Make sure request exists / is valid
    group_request = get_request(request_id, group_id)
    if group_request is None:
        flash("Unauthorized or invalid request", "danger")
        return redirect(url_for('main.inbox'))
    
    # verify current user is owner of group 
    group = StudyGroup.query.get(group_request.group_id)
    if current_user.id != group.owner_id:
        flash("You are not the owner of this group", "danger")
        return redirect(url_for('main.inbox'))
    
    user = User.query.get(group_request.user_id)
    
    GroupJoinRequest.reject(group_request)
    db.session.commit()

    flash(f"You have rejected {user.name}'s request to join {group.name}", "info")
    return redirect(url_for('main.inbox'))

@main_bp.route('/cancel-request/<request_id>', methods=["POST"])
@login_required
def cancel_request(request_id):
    # Check if request exists
    group_request = GroupJoinRequest.query.get(request_id)
    if not group_request:
        flash("Unauthorized or invalid request", "danger")
        return redirect(url_for('main.inbox'))
    
    db.session.delete(group_request)
    db.session.commit()
    flash("Request canceled.", "info")
    return redirect(url_for('main.inbox'))
    

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

@main_bp.route('/search-groups')
def search_groups():
    query = request.args.get('q', '').lower()

    owner_alias = aliased(User)

    filtered_groups = db.session.query(StudyGroup).join(owner_alias, StudyGroup.owner).filter(
        or_(
            StudyGroup.name.ilike(f"%{query}%"),
            StudyGroup.description.ilike(f"%{query}%"),
            owner_alias.name.ilike(f"%{query}%")
        )
    ).all()
    
    return render_template('find-groups.html', study_groups=filtered_groups)

@main_bp.route("/profile")
@login_required
def profile():
    user = current_user
    return render_template('profile.html', user=user)

@main_bp.route("/edit-profile", methods=['POST'])
@login_required
def edit_profile():
    bio = request.form.get("bio")
    major = request.form.get("major")
    year = request.form.get("year")

    VALID_YEARS = ['Freshman', 'Sophomore', 'Junior', 'Senior', 'Graduate']

    if year not in VALID_YEARS:
        flash("Invalid year selected.", "danger")
        return redirect(url_for('main.profile'))

    fields_to_update = {
        'bio': bio,
        'major': major,
        'year': year,
    }

    updated_fields = []

    print(f"To Update: {fields_to_update}")

    for field, new_value in fields_to_update.items():
        current_value = getattr(current_user, field)
        if new_value and new_value != current_value:
            setattr(current_user, field, new_value)
            print(f"({current_user.name}):  {field}: {new_value}")
            updated_fields.append(field)

    print(f"Updated: {updated_fields}")

    try:
        db.session.commit()
        if updated_fields:
            flash("Profile updated successfully!", "success")
        else:
            flash("No changes were made.", "info")
    except Exception as e:
        db.session.rollback()
        print(f"Profile Update Error: {e}")
        flash("An unexpected error occurred. Please try again later.", "danger")
        return redirect(url_for('main.profile'))


    return redirect(url_for('main.profile'))

@main_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    if current_user.is_google_user == 1:
        flash("You are registered with Google SSO and must change you're password through their services", "danger")
        return redirect(url_for('main.profile'))

    current_password = request.form.get("current-password")
    new_password = request.form.get("new-password")
    new_confirm_password = request.form.get("new-confirm-password")

    if not current_password or not new_password or not new_confirm_password:
        flash("All fields are required", "danger")
        return redirect(url_for('main.profile'))
    
    if not current_user.check_password(current_password):
        flash("Current password is incorrect", "danger")
        return redirect(url_for('main.profile'))
    
    if new_password != new_confirm_password:
        flash("New password and confirm password don't match", "danger")
        return redirect(url_for('main.profile'))
    
    if not is_valid_password(new_password):
            flash("Password must be at least 8 characters long and include one letter, one number, and one special character.", "danger")
            return redirect(url_for('main.profile'))
    
    current_user.set_password(new_password)
    db.session.commit()

    flash("Password updated successfully.", "success")
    return redirect(url_for('main.profile'))


@main_bp.route("/map")
@login_required
def map():
    return render_template('map.html', ACCESS_KEY=MAPBOX_ACCESS_KEY)

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


@main_bp.route("/group-request", methods=['POST'])
@login_required
def group_request():
    group_id = request.form.get("group_id")

    if not group_id:
        flash("Invalid Group ID.", 'danger')
        return redirect(url_for('main.find_groups'))
    
    # Check if group exists
    group = StudyGroup.query.filter_by(id=group_id).first()
    if not group:
        flash("Study group not found!", "danger")
        return redirect(url_for('main.find_groups'))
    
    # check if user is already in group
    if current_user in group.members:
        flash("You are already a member of this group.", "danger")
        return redirect(url_for('main.find_groups'))
    
    # check if user already has a pending request
    group_request = GroupJoinRequest.query.filter(
        GroupJoinRequest.user_id == current_user.id,
        GroupJoinRequest.group_id == group.id,
        GroupJoinRequest.status == 'pending'
    ).first()
    if group_request:
        flash("You already have a pending request for this group.", "info")
        return redirect(url_for('main.find_groups'))

    # create request for group in table
    new_request = GroupJoinRequest(user_id=current_user.id, group_id=group_id)
    db.session.add(new_request)
    db.session.commit()

    flash(f"You have requested to join { group.name }!", "info")
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

@main_bp.route("/edit-group/<int:group_id>", methods=['POST'])
@login_required
def edit_group(group_id):
    if not group_id:
        flash("Invalid Group ID", "danger")
        return redirect(url_for('main.my_groups'))
    
    if not isinstance(group_id, int):
        flash("Invalid Group ID format." "danger")
        return redirect('main.my_groups')
    
    # check if group exists
    group = StudyGroup.query.filter_by(id=group_id).first()
    if not group:
        flash("Study group not found!", "danger")
        return redirect(url_for('main.my_groups'))
    
    # Check if user is owner of group
    if group.owner_id != current_user.id:
        flash("You are not the owner of this group.", "danger")
        return redirect(url_for('main.my_groups'))
    
    name = request.form.get("name")
    subject = request.form.get("subject")
    description = request.form.get("description")
    location = request.form.get("location")

    # Validate input
    if name and len(name) > 100:
        flash("Group name must not exceed 100 characters." "danger")
        return redirect(url_for('main.edit_group', group_id=group_id))
    
    fields_to_update = {
        'name': name,
        'subject': subject,
        'description': description,
        'location': location
    }

    updated_fields = []

    for field, new_value in fields_to_update.items():
        current_value = getattr(group, field)
        if new_value and new_value != current_value:
            setattr(group, field, new_value)
            updated_fields.append(field)

    try:
        db.session.commit()
        if updated_fields:
            flash("Group updated successfully!", "success")
        else:
            flash("No changes were made.", "info")
    except Exception as e:
        db.session.rollback()
        flash("An unexpected error occurred. Please try again later.", "danger")

    return redirect(url_for('main.manage_group', group_id=group_id))
    

@main_bp.route("/remove-member/<group_id>/<member_id>", methods=['POST'])
@login_required
def remove_member(group_id, member_id):
    if not member_id or not group_id:
        flash("Invalid member or group ID", "danger")
        return redirect(url_for('main.manage_group', group_id=group_id))
    
    member = User.query.get(member_id)
    if not member:
        flash("Member not found", "danger")
        return redirect(url_for('main.manage_group', group_id=group_id))
    
    group = StudyGroup.query.get(group_id)
    if not group:
        flash("Group not found", "danger")
        return redirect(url_for('main.manage_group', group_id=group_id))
    
    try:
        group.members.remove(member)
        group.current_members -= 1
        db.session.commit()
        flash(f"You have removed {member.name} from the group", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occured: {str(e)}", "danger")

    return redirect(url_for('main.manage_group', group_id=group_id))    


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
    
    # Check if group exists 
    if group == None:
        flash("This group doesn't exist", "danger")
        return redirect(url_for('main.my_groups'))

    if current_user.id != group.owner_id:
        flash("You do not have permission to delete this group", "danger")
        return redirect(url_for('main.my_groups'))
    
    group.members.clear()
    db.session.delete(group)
    db.session.commit()

    flash(f"Study group '{group.name}' deleted successfully", "success")
    return redirect(url_for('main.my_groups'))




