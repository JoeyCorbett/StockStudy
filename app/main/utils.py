from app.models.membership_requests import GroupJoinRequest

def get_request(request_id, group_id):
    return GroupJoinRequest.query.filter_by(
        id=request_id,
        group_id=group_id,
        status='pending'
    ).first()