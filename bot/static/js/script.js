document.addEventListener('DOMContentLoaded', function () {
    // Obtener el formulario y los campos de entrada
    const addFolderForm = document.querySelector('form[action="/add_folder"]');
    const folderNameInput = document.querySelector('#folder_name');
    const folderIdInput = document.querySelector('#folder_id');

    // Agregar evento para validar el formulario antes de enviarlo
    addFolderForm.addEventListener('submit', function (event) {
        if (folderNameInput.value.trim() === '' || folderIdInput.value.trim() === '') {
            event.preventDefault(); // Evitar que se envíe el formulario
            alert('Por favor, completa ambos campos antes de enviar.');
        }
    });

    // Obtener el botón de descargar Excel
    const downloadForm = document.querySelector('form[action="/download_excel"]');
    const folderSelect = document.querySelector('#folder_name_select');

    // Asegurarse de que se haya seleccionado una carpeta antes de descargar
    downloadForm.addEventListener('submit', function (event) {
        if (folderSelect.value.trim() === '') {
            event.preventDefault(); // Evitar que se envíe el formulario
            alert('Por favor, selecciona una carpeta antes de descargar el Excel.');
        }
    });
});
