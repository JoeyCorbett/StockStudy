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
    deleteForm.action =  `/delete-group/${groupID}`;
}