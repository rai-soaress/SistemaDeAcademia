function confirmarExclusao() {
    return confirm("Tem certeza que deseja excluir?");
}

document.addEventListener("DOMContentLoaded", function () {
    const deleteLinks = document.querySelectorAll("a[data-confirm]");

    deleteLinks.forEach(function (link) {
        link.addEventListener("click", function (event) {
            const message = link.dataset.confirm || "Tem certeza que deseja excluir?";

            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });

    const confirmButtons = document.querySelectorAll("button[data-confirm]");

    confirmButtons.forEach(function (button) {
        button.addEventListener("click", function (event) {
            const message = button.dataset.confirm || "Confirmar acao?";

            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });
});
