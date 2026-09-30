document.querySelectorAll('input[type="password"]').forEach((campo, indice) => {
    if (!campo.id) campo.id = `senha-${indice}`;
    const grupo = document.createElement('div');
    grupo.className = 'campo-senha';
    campo.before(grupo);
    grupo.append(campo);
    const botao = document.createElement('button');
    botao.type = 'button';
    botao.className = 'alternar-senha';
    botao.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/><path class="risco-olho" d="m3 3 18 18"/></svg>';
    botao.setAttribute('aria-label', 'Mostrar senha');
    botao.title = 'Mostrar senha';
    botao.setAttribute('aria-controls', campo.id);
    botao.setAttribute('aria-pressed', 'false');
    botao.addEventListener('click', () => {
        const mostrar = campo.type === 'password';
        campo.type = mostrar ? 'text' : 'password';
        const descricao = mostrar ? 'Ocultar senha' : 'Mostrar senha';
        botao.setAttribute('aria-label', descricao);
        botao.title = descricao;
        botao.setAttribute('aria-pressed', String(mostrar));
    });
    grupo.append(botao);
});
