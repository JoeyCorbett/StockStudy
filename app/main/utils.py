from app.models.membership_requests import GroupJoinRequest
from app.models.study_group import StudyGroup
from app.models.group_invites import GroupInvites
from app.extensions import db


def get_request(request_id, group_id):
    return GroupJoinRequest.query.filter_by(
        id=request_id,
        group_id=group_id,
        status='pending'
    ).first()

def validate_invite(invite_id, user_id, type):
    if not invite_id:
        raise ValueError("Invite ID not received.")
    
    # verify invite exists
    invite = GroupInvites.query.get(invite_id)
    if not invite:
        raise ValueError("Invite not found. Please try again.")
    
    if type not in ['incoming', 'outgoing']:
        raise ValueError("Invalid invite type.")

    if type == 'incoming':
        # verify invite belongs to receiving user
        if invite.invitee_id != user_id:
            raise PermissionError("Unauthorized access to this invite.")
    else:
        # verify invite belongs to sending user
        if invite.inviter_id != user_id:
            raise PermissionError("Unauthorized access to this invite.")

    # verify invite has pending status
    if invite.status != 'pending':
        raise ValueError("This invite is no longer valid.")

    # check if group exists
    group = StudyGroup.query.filter_by(id=invite.group_id).first()
    if not group:
        raise ValueError("The group doesn't exist.")
      
    # get members in group
    members = [member.id for member in group.members]
    if invite.invitee_id in members:
        raise ValueError("You're already a member in this group.")
    
    # check if invite is expired
    if invite.is_expired():
        db.session.delete(invite)
        db.session.commit()
        raise ValueError("This invite is expired.")
    
    return invite