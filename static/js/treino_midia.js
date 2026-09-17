(() => {
    const modal = document.createElement("dialog");
    modal.className = "media-modal";
    modal.setAttribute("aria-label", "Midia do treino");

    const voltar = document.createElement("button");
    voltar.type = "button";
    voltar.className = "modal-close";
    voltar.textContent = "Voltar ao treino";
    voltar.addEventListener("click", () => modal.close());

    const conteudo = document.createElement("div");
    modal.append(voltar, conteudo);
    document.body.append(modal);

    modal.addEventListener("close", () => conteudo.replaceChildren());

    document.addEventListener("click", (event) => {
        const link = event.target.closest("a[data-treino-midia]");
        if (!link) return;
        event.preventDefault();

        const video = link.dataset.treinoMidia === "video";
        const midia = document.createElement(video ? "video" : "img");
        midia.src = link.href;
        if (video) midia.controls = true;
        else midia.alt = "Midia do exercicio";
        conteudo.replaceChildren(midia);
        modal.showModal();
    });
})();
