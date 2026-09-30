document.querySelectorAll('input[type="password"]').forEach((campo, indice) => {
    if (!campo.id) campo.id = `senha-${indice}`;
    const botao = document.createElement('button');
    botao.type = 'button';
    botao.className = 'alternar-senha';
    botao.textContent = 'Mostrar senha';
    botao.setAttribute('aria-controls', campo.id);
    botao.setAttribute('aria-pressed', 'false');
    botao.addEventListener('click', () => {
        const mostrar = campo.type === 'password';
        campo.type = mostrar ? 'text' : 'password';
        botao.textContent = mostrar ? 'Ocultar senha' : 'Mostrar senha';
        botao.setAttribute('aria-pressed', String(mostrar));
    });
    campo.insertAdjacentElement('afterend', botao);
});
