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


function searchUsers(query) {
    const inviteMemberModal = document.getElementById('inviteMemberModal');

    inviteMemberModal.addEventListener('hidden.bs.modal', () => {
        document.getElementById('searchUser').value = '';
        document.getElementById('searchResults').innerHTML = '';
    });

    const resultsContainer = document.getElementById('searchResults');
    button = document.querySelector('.btn-group-id')
    groupID = button.getAttribute('data-group-id');

    fetch(`/search/users?query=${query}&group_id=${groupID}`)
        .then(response => response.json())
        .then(users => {
            if (users.length === 0) {
                resultsContainer.innerHTML = `
                    <li class="list-group-item text-center text-muted">
                        No users found.
                    </li>
                `;
                return;
            }
            resultsContainer.innerHTML = users.map(user => `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    <span class="fw-semibold">${user.name} (${user.email})</span>
                    ${
                        user.invited
                            ? '<span class="badge bg-secondary py-2">Invited</span>'
                            : `<button class="btn btn-primary btn-sm invite-btn" onclick="inviteUser('${user.email}', '${groupID}', this)">Invite</button>`
                    }
                </li>
            `).join('');
        })
        .catch(error => console.error('Error fetching users:', error));
}

let isInviting = false;

async function inviteUser(email, group_id, button) {
    if (isInviting) return ;
    isInviting = true;

    try {
        const response = await fetch(`/invite/${group_id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "An error occurred");
        }

        button.outerHTML = '<span class="badge bg-secondary py-2">Invited</span>';
    } catch (error) {
        console.error('Error inviting user:', error);
    } finally {
        isInviting = false;
    }
}
