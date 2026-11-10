// Open the modal and display the clicked image
function openModal(imageSrc) {
    const modal = document.getElementById('image-modal');
    const modalImage = document.getElementById('modal-image');
    modalImage.src = imageSrc;
    modal.style.display = 'block';
}

// Close the modal
function closeModal() {
    const modal = document.getElementById('image-modal');
    modal.style.display = 'none';
}
