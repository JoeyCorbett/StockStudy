async function copyToClipboard(email, buttonElement) {
    try {
        await navigator.clipboard.writeText(email);

        buttonElement.textContent = "Copied!";
        setTimeout(() => {
            buttonElement.textContent = "Contact";
        }, 2000);
    } catch (err) {
        console.error("Failed to copy email")
        buttonElement.textContent = "Failed to Copy";
    }
}

function setDeleteAction(groupID) {
    const deleteForm = document.getElementById('deleteGroupForm');
    deleteForm.action = `/delete-group/${groupID}`;
}

function setLeaveAction(groupID) {
    const leaveForm = document.getElementById('leaveGroupForm');
    leaveForm.action = `/leave-group/${groupID}`;
}

function setRemoveAction(groupID, memberID) {
    const removeForm = document.getElementById('removeMemberForm')
    removeForm.action = `/remove-member/${groupID}/${memberID}`;
}

document.addEventListener('show.bs.modal', function (event) {
    const modal = event.target;

    if (modal.id == 'quickViewModal') {
        const button = event.relatedTarget;

        const groupId = button.getAttribute('data-group-id');
        const groupName = button.getAttribute('data-group-name');
        const groupSubject = button.getAttribute('data-group-subject');
        const groupOwner = button.getAttribute('data-group-owner');
        const groupDescription = button.getAttribute('data-group-description');
        const groupType = button.getAttribute('data-group-type');
        const groupMembers = button.getAttribute('data-group-members');
        const groupLocation = button.getAttribute('data-group-location');


        modal.querySelector('.modal-title').textContent = groupName;
        modal.querySelector('.modal-subject').textContent = groupSubject;
        modal.querySelector('.modal-owner').textContent = groupOwner;
        modal.querySelector('.modal-description').textContent = groupDescription;
        modal.querySelector('.modal-type').textContent = groupType;
        modal.querySelector('#modal-members-list').textContent = groupMembers;
        modal.querySelector('.modal-location').textContent = groupLocation;
    }
});