console.log("EthosTeoInclusiva carregado.");

/**
 * AJUSTE 1 (recomendado):
 * Coloque id="resposta" no container da resposta.
 * Ex:
 * <div id="resposta" class="card">...</div>
 */

function findRespostaEl() {
  // Melhor caso: id fixo
  let el = document.getElementById("resposta");
  if (el) return el;

  // Alternativas comuns (se seu HTML usa classes)
  el = document.querySelector(".resposta, .answer, .faq-answer");
  if (el) return el;

  // Último recurso: achar um bloco que tenha um título "Resposta"
  const headings = Array.from(document.querySelectorAll("h1,h2,h3,div,strong"));
  const h = headings.find(node => (node.textContent || "").trim().toLowerCase() === "resposta");
  if (h) {
    // tenta pegar o próximo bloco relevante
    return h.closest(".card") || h.parentElement;
  }

  return null;
}

function flashResposta(el) {
  if (!el) return;
  const old = el.style.boxShadow;
  const oldBorder = el.style.borderColor;

  el.style.transition = "box-shadow .25s ease, border-color .25s ease";
  el.style.boxShadow = "0 0 0 4px rgba(0,176,255,.20), 0 16px 32px rgba(0,0,0,.12)";
  el.style.borderColor = "rgba(0,176,255,.55)";

  setTimeout(() => {
    el.style.boxShadow = old;
    el.style.borderColor = oldBorder;
  }, 900);
}

function scrollToResposta() {
  const el = findRespostaEl();
  if (!el) return;

  // Scroll suave até a resposta
  el.scrollIntoView({ behavior: "smooth", block: "start" });

  // Destaque rápido pra orientar o usuário
  flashResposta(el);
}

// Heurística: o clique em "pergunta" costuma ser link/botão dentro da área de perguntas.
// Aqui eu capturo:
const POSSIVEIS_SELETORES_DE_PERGUNTA = [
  ".faq-question",
  ".qa-item",
  ".question-list a",
  ".lista-perguntas a",
  ".questions a",
  // fallback: qualquer link dentro do card de perguntas
  ".card a"
].join(", ");

// 1) Quando clicar numa pergunta, a resposta pode atualizar depois (via navegação/hash/render).
// Então: esperamos um pouquinho e scrollamos.
document.addEventListener("click", (e) => {
  const alvo = e.target.closest(POSSIVEIS_SELETORES_DE_PERGUNTA);
  if (!alvo) return;

  // Se for um link âncora que vai pra outro lugar, não atrapalha.
  // Se for navegação interna, geralmente a resposta aparece na mesma página.
  setTimeout(scrollToResposta, 80);
});

// 2) Se sua página atualiza resposta ao mudar hash (#algo) ou rota,
// rola também quando ocorrer mudança.
window.addEventListener("hashchange", () => {
  setTimeout(scrollToResposta, 80);
});

// 3) Se seu site renderiza a resposta trocando o HTML dinamicamente,
// um MutationObserver garante que quando a resposta mudar, ela suba na tela.
const observer = new MutationObserver((mutations) => {
  // Se qualquer coisa mudou dentro do container da resposta, rola.
  const el = findRespostaEl();
  if (!el) return;

  // Se houve mudança dentro da resposta, scrolla (com pequena tolerância)
  const mudouResposta = mutations.some(m => el.contains(m.target));
  if (mudouResposta) {
    setTimeout(scrollToResposta, 50);
  }
});

observer.observe(document.body, { childList: true, subtree: true });