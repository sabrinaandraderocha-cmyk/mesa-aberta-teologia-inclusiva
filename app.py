import os
import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, jsonify

# =====================================================
# CONFIGURAÇÕES
# =====================================================
APP_NAME = "Mesa Aberta - Teologia Inclusiva"
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-ethos-teo-inclusiva-secret-v1")

DATA_DIR = os.path.abspath("./data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "ethos_teo_inclusiva.sqlite3")

FOOTER_VERSE = "Deus não faz acepção de pessoas. (Atos 10:34)"
FOOTER_VERSE_URL = "https://www.bibliaonline.com.br/nvi/atos/10/34"
VERSE_OF_DAY_API = "https://beta.ourmanna.com/api/v1/get?format=json&order=daily"

# Adicionado o Disclaimer Global
DISCLAIMER = "Esse app é cristão protestante, mas é contra qualquer tipo de intolerância religiosa."

# =====================================================
# LINKS ÚTEIS (BRASIL)
# =====================================================
LINKS_UTEIS = {
    "disque_100": "https://www.gov.br/pt-br/servicos/denunciar-violacao-de-direitos-humanos",
    "ondh": "https://www.gov.br/mdh/pt-br/ondh",
    "safernet_denuncie": "https://new.safernet.org.br/denuncie",
    "cvv": "https://cvv.org.br/",
}

# =====================================================
# HELPERS DE RESPOSTA (HTML)
# =====================================================
def _html_escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _normalize_key(s: str) -> str:
    if not s:
        return ""
    return (
        s.replace("—", "-")
         .replace("–", "-")
         .replace("−", "-")
         .strip()
    )

def _make_answer(title: str, bullets: list[str], refs: list[str] | None = None, delicate: bool = True) -> str:
    warn = ""
    if delicate:
        warn = """
        <div class="alert-box warning">
          <strong>Cuidado pastoral:</strong> este tema pode envolver culpa, medo ou trauma religioso.
          Se você está em sofrimento, procure acolhimento seguro (comunidade inclusiva, terapia, rede de apoio).
          Em risco imediato, busque ajuda local de emergência.
        </div>
        """
    lis = "".join([f"<li>{_html_escape(b)}</li>" for b in bullets if (b or "").strip()])
    refs_html = ""
    if refs:
        refs_html = "<div class='refs'><strong>Referências bíblicas:</strong> " + ", ".join([_html_escape(r) for r in refs]) + "</div>"

    return f"""
    <div class="resposta-humanizada">
      <h3>{_html_escape(title)}</h3>
      {warn}
      <ul>{lis}</ul>
      {refs_html}
    </div>
    """

def _make_links_block(items: list[tuple[str, str]]) -> str:
    lis = "".join([
        f"<li><a href='{_html_escape(url)}' target='_blank' rel='noopener'>{_html_escape(label)}</a></li>"
        for label, url in items
    ])
    return f"<div class='links-box'><strong>Links úteis:</strong><ul>{lis}</ul></div>"

def fetch_verse_of_day() -> dict:
    fallback = {
        "text": "O Senhor é bom, uma fortaleza no dia da angústia; e conhece os que confiam nele.",
        "reference": "Naum 1:7",
        "source_url": "https://beta.ourmanna.com/"
    }
    try:
        import urllib.request
        import json
        req = urllib.request.Request(VERSE_OF_DAY_API, headers={"accept": "application/json"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        details = (((data or {}).get("verse") or {}).get("details") or {})
        text = (details.get("text") or "").strip()
        reference = (details.get("reference") or "").strip()
        if text and reference:
            return {"text": text, "reference": reference, "source_url": "https://beta.ourmanna.com/api/v1/get"}
        return fallback
    except Exception:
        return fallback

@app.context_processor
def inject_globals():
    return {
        "verse_of_day": fetch_verse_of_day(),
        "footer_verse_url": FOOTER_VERSE_URL,
        "disclaimer": DISCLAIMER,
    }

# =====================================================
# BANCO (LOG SIMPLES DE CONSULTAS)
# =====================================================
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS query_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()

init_db()

def log_question(q: str):
    if not q:
        return
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO query_log (question, created_at) VALUES (?, ?)",
            (q, datetime.utcnow().isoformat(timespec="seconds"))
        )
        conn.commit()

# =====================================================
# LISTA DE PERGUNTAS (ORDEM DE EXIBIÇÃO)
# =====================================================
QUICK_QUESTIONS = [
    # TEMAS PRINCIPAIS
    "É pecado ser homossexual?",
    "A Bíblia fala de orientação sexual como conhecemos hoje?",
    "E as passagens de Levítico (Lv 18:22; 20:13)?",
    "E Romanos 1 (Rm 1:26–27)?",
    "E 1 Coríntios 6:9–10 (malakoi / arsenokoitai)?",
    "E 1 Timóteo 1:10 (arsenokoitai)?",
    "E Judas 7 e 'carne estranha'?",
    "E a história de Sodoma (Gênesis 19) é sobre o quê?",
    "O que Deus pensa de mim, se eu sou LGBTQIA+?",
    "A Bíblia fala sobre pessoas trans?",
    "E Deuteronômio 22:5 sobre usar roupas do 'sexo oposto'?",
    "Mudar o corpo (transição) é 'destruir o templo do Espírito'?",
    "Deus errou ao criar uma pessoa trans?",
    
    # CURIOSIDADES BÍBLICAS (Novas adições!)
    "🔍 Maria Madalena era prostituta?",
    "🔍 A Lei de Talião ('olho por olho') era justiça literal?",
    "🔍 Qual idioma Jesus falava?",
    "🔍 Quem dividiu a Bíblia em capítulos e versículos?",

    # AJUDA E ACOLHIMENTO
    "Como lidar com culpa e medo por causa da religião?",
    "Como responder com amor quando alguém usa a Bíblia para ferir?",
    "Precisa de ajuda contra homofobia? (Denúncias e direitos)",
    "Precisa de ajuda espiritual? (Igrejas inclusivas)",
    "Precisa de ajuda psicológica agora? (CVV e clínicas-escola)",
    "O que significa 'Deus não faz acepção de pessoas'?"
]

# =====================================================
# RESPOSTAS (TEOLOGIA INCLUSIVA: PASTORAL, DIRETA, ACADÊMICA)
# =====================================================
RESPOSTAS_DB = {
    # --- RESPOSTAS ORIGINAIS ---
    "É pecado ser homossexual?": _make_answer(
        "Não: a Bíblia não condena 'ser' LGBTQIA+ como identidade/orientação.",
        [
            "A categoria moderna de orientação/identidade sexual não aparece no texto bíblico como conceito psicológico-social contemporâneo.",
            "As passagens usadas para condenar pessoas LGBTQIA+ descrevem, em muitos casos, práticas de violência, exploração, humilhação, idolatria ritual ou abuso de poder - não amor fiel, consentido e responsável.",
            "Uma ética cristã centrada em Jesus avalia frutos: amor, justiça, misericórdia, cuidado e verdade (não medo e opressão).",
            "Você não precisa escolher entre fé e dignidade: Deus acolhe pessoas, não rótulos usados para excluir."
        ],
        refs=["Atos 10:34-35", "Gálatas 3:28", "Mateus 7:16-20", "Mateus 22:37-40"],
        delicate=True
    ),

    "A Bíblia fala de orientação sexual como conhecemos hoje?": _make_answer(
        "Não do mesmo modo: o mundo bíblico descreve atos em contextos sociais distintos.",
        [
            "No mundo antigo, sexualidade frequentemente se relacionava a status, honra/vergonha, dominação e desigualdade (senhor/escravo, adulto/jovem, cidadão/não-cidadão).",
            "Por isso, várias proibições se conectam a exploração, prostituição cultual, abuso e práticas de humilhação.",
            "Pergunta pastoral e ética: há consentimento, fidelidade, cuidado mútuo, justiça e ausência de violência?",
            "Leituras inclusivas se apoiam em método histórico-cultural e na centralidade do amor ao próximo como critério moral."
        ],
        refs=["Mateus 22:37-40", "Gálatas 5:14", "1 Samuel 16:7"],
        delicate=False
    ),

    "E as passagens de Levítico (Lv 18:22; 20:13)?": _make_answer(
        "Leituras inclusivas situam Levítico em leis de pureza/santidade, não como condenação universal de pessoas LGBTQIA+.",
        [
            "Levítico integra um código com diversas normas rituais (alimentação, tecidos, contato, ciclos), voltadas à identidade comunitária de Israel antigo.",
            "Há interpretações de que o alvo inclui práticas associadas a culto, dominação/humilhação e desordem ritual - não relações amorosas e igualitárias.",
            "Mesmo cristãos que citam Levítico costumam não aplicar literalmente outras regras do mesmo corpus; isso exige coerência hermenêutica.",
            "No Novo Testamento, a lei é lida à luz de Cristo e do amor que cumpre a lei (priorizando misericórdia e justiça)."
        ],
        refs=["Levítico 18:22", "Levítico 20:13", "Marcos 7:18-23", "Gálatas 5:14"],
        delicate=True
    ),

    "E Romanos 1 (Rm 1:26–27)?": _make_answer(
        "Romanos 1 está dentro de uma crítica à idolatria e à degradação ética; não é um tratado sobre orientação sexual.",
        [
            "O trecho aparece em um argumento sobre idolatria e suas consequências sociais (Rm 1:18-32).",
            "Leituras inclusivas entendem que Paulo descreve práticas de excesso e desordem ligadas ao contexto pagão do império (frequentemente marcadas por exploração e abuso).",
            "Paulo usa isso para preparar o ponto seguinte: ninguém deve se colocar como juiz do outro (Rm 2:1).",
            "Assim, o texto não autoriza condenar relações amorosas, fiéis e consentidas; o alvo é a injustiça e a ruptura ética que desumaniza."
        ],
        refs=["Romanos 1:18-32", "Romanos 2:1", "Romanos 3:23-24"],
        delicate=True
    ),

    "E 1 Coríntios 6:9–10 (malakoi / arsenokoitai)?": _make_answer(
        "Aqui o debate é de tradução: esses termos não equivalem diretamente a 'homossexualidade' moderna.",
        [
            "Algumas traduções modernas usam 'homossexuais', mas isso é uma escolha interpretativa: os termos gregos são complexos e contextualizados.",
            "Leituras inclusivas frequentemente leem o par de termos em relação a exploração sexual, abuso e práticas degradantes, comuns em sociedades hierárquicas.",
            "O contexto de Corinto envolve desigualdade, abuso e confusões morais; a lista de vícios aponta para injustiças que ferem o próximo.",
            "O movimento do texto é restaurativo: 'fostes lavados…' (dignidade e recomeço, não autorização para humilhar)."
        ],
        refs=["1 Coríntios 6:9-11"],
        delicate=True
    ),

    "E 1 Timóteo 1:10 (arsenokoitai)?": _make_answer(
        "O termo é raro e aparece em lista de abusos; leituras inclusivas o ligam a exploração/violência, não a identidade.",
        [
            "A lista de 1Tm 1 é sobre comportamentos que ferem a vida comunitária e a justiça (violência, mentira, abuso).",
            "O termo arsenokoitai é discutido na literatura: pode se referir a práticas exploratórias, comércio sexual, coerção e abuso de poder.",
            "Pastoralmente: a carta visa proteger a comunidade de abusos, não criar categoria para excluir pessoas por orientação/identidade.",
            "O critério ético permanece: amor que não causa dano ao próximo."
        ],
        refs=["1 Timóteo 1:8-11", "Romanos 13:10"],
        delicate=True
    ),

    "E Judas 7 e 'carne estranha'?": _make_answer(
        "Leituras inclusivas entendem 'carne estranha' em conexão com violência, transgressão e abuso - não orientação sexual.",
        [
            "Judas usa exemplos de julgamento ligados a rebelião, opressão e desordem moral, em linguagem forte e simbólica.",
            "A expressão é interpretada por muitos como referência a transgressões graves, inclusive violência e tentativa de abuso (não uma descrição de relações consentidas).",
            "O texto funciona como alerta contra líderes e práticas que corrompem a comunidade e produzem dano.",
            "Pastoralmente: não use Judas como arma; use como chamado à responsabilidade e à proteção dos vulneráveis."
        ],
        refs=["Judas 7", "Judas 8-16"],
        delicate=True
    ),

    "E a história de Sodoma (Gênesis 19) é sobre o quê?": _make_answer(
        "Sodoma é, sobretudo, sobre violência e humilhação do estrangeiro - não sobre amor entre pessoas do mesmo sexo.",
        [
            "O episódio descreve uma tentativa de violência coletiva contra visitantes; isso é abuso e desumanização, não relação afetiva.",
            "Profetas associam Sodoma a injustiça social, arrogância e negligência com pobres e vulneráveis.",
            "Usar Sodoma para condenar pessoas LGBTQIA+ desloca o foco do texto e apaga a denúncia bíblica contra violência e opressão.",
            "Pastoralmente: Deus condena a violência e a exclusão; Deus acolhe quem é ferido por elas."
        ],
        refs=["Gênesis 19", "Ezequiel 16:49-50", "Isaías 1:10-17"],
        delicate=True
    ),

    "O que Deus pensa de mim, se eu sou LGBTQIA+?": _make_answer(
        "Deus vê você por inteiro: amado(a), digno(a) e chamado(a) à vida plena.",
        [
            "O coração do evangelho não é rejeição, mas reconciliação, cura e pertencimento.",
            "A Bíblia mostra Deus atravessando fronteiras de pureza social para acolher pessoas marginalizadas.",
            "Seu valor não depende do que líderes ou comunidades disseram para te controlar; depende do amor de Deus.",
            "Vocação cristã: viver verdade, amor e justiça - com integridade e cuidado."
        ],
        refs=["Salmo 139:13-14", "Romanos 8:38-39", "Atos 10:34-35"],
        delicate=True
    ),

    # --- RESPOSTAS SOBRE PESSOAS TRANS ---
    "A Bíblia fala sobre pessoas trans?": _make_answer(
        "A Bíblia não usa o conceito moderno de transgeneridade, mas possui fortes princípios de diversidade e acolhimento.",
        [
            "Gênesis descreve a criação em extremos (dia/noite, terra/mar, macho/fêmea). Assim como existe o crepúsculo e os pântanos, o ser humano também existe em um vasto e belo espectro biológico e identitário.",
            "No mundo antigo, os 'eunucos' ocupavam um espaço fora do binarismo tradicional de gênero e, muitas vezes, eram marginalizados.",
            "Deus, através do profeta Isaías, promete aos eunucos um lugar de honra no Seu templo, quebrando a exclusão religiosa da época.",
            "Jesus reafirma esse acolhimento (Mateus 19), mostrando que o Reino de Deus tem espaço para corpos e vivências que fogem à norma da sociedade."
        ],
        refs=["Isaías 56:4-5", "Mateus 19:12", "Gálatas 3:28"],
        delicate=True
    ),

    "E Deuteronômio 22:5 sobre usar roupas do 'sexo oposto'?": _make_answer(
        "O texto trata de códigos de pureza ritual e separação da época, não de identidade de gênero.",
        [
            "As leis do Antigo Testamento frequentemente separavam coisas (tecidos, sementes, animais) para manter uma ordem ritual específica de Israel, diferenciando-os de nações vizinhas.",
            "O vestuário da época era muito diferente do atual. Muitos estudiosos veem essa regra como uma proibição de disfarces para fraudes ou práticas de idolatria militar.",
            "Aplicar uma lei de pureza ritual de milênios atrás para invalidar a vivência de pessoas trans hoje é um erro teológico e exegético."
        ],
        refs=["Deuteronômio 22:5", "Colossenses 2:16-17"],
        delicate=False
    ),

    "Mudar o corpo (transição) é 'destruir o templo do Espírito'?": _make_answer(
        "Modificar o corpo para cura, adequação e bem-estar não é destruí-lo, é cuidar da vida que Deus deu.",
        [
            "A medicina moderna nos permite tratar o sofrimento humano. Para pessoas trans, a transição é frequentemente um cuidado vital para tratar a disforia de gênero.",
            "O alerta sobre o 'templo do Espírito' em 1 Coríntios 6 refere-se a não usar o corpo para explorar, violentar ou ferir o próximo (e a si mesmo) em práticas injustas.",
            "Cuidar da sua saúde mental e física, alinhando seu corpo à sua identidade, é um ato de respeito e preservação da própria vida."
        ],
        refs=["1 Coríntios 6:19-20", "Efésios 5:29"],
        delicate=True
    ),

    "Deus errou ao criar uma pessoa trans?": _make_answer(
        "Deus não erra. A diversidade humana, incluindo a transgeneridade, reflete a vastidão criativa de Deus.",
        [
            "A biologia, a genética e a neurobiologia mostram que o desenvolvimento do sexo e do gênero é incrivelmente complexo.",
            "Como dizem alguns teólogos inclusivos: 'Deus criou o trigo, mas nós fazemos o pão; Deus criou a uva, mas nós fazemos o vinho'.",
            "Sua transgeneridade não é um defeito ou um castigo. É uma das muitas formas maravilhosas pelas quais a humanidade reflete a imagem divina."
        ],
        refs=["Salmo 139:13-16", "1 Samuel 16:7"],
        delicate=True
    ),

    # --- CURIOSIDADES BÍBLICAS ---
    "🔍 Maria Madalena era prostituta?": _make_answer(
        "Não! A Bíblia nunca a chama de prostituta. Esse é um erro histórico.",
        [
            "Maria Madalena foi uma das seguidoras mais fiéis de Jesus, uma líder fundamental e a primeira testemunha da ressurreição.",
            "A confusão começou no ano 591, quando o Papa Gregório I misturou, em um sermão, três mulheres diferentes: Maria Madalena, Maria de Betânia e a 'mulher pecadora' anônima que ungiu os pés de Jesus (Lucas 7).",
            "Apenas em 1969 a Igreja Católica corrigiu oficialmente esse erro, separando as identidades dessas mulheres, mas a imagem popular da prostituta já havia se espalhado."
        ],
        refs=["Lucas 8:2", "João 20:11-18"],
        delicate=False
    ),

    "🔍 A Lei de Talião ('olho por olho') era justiça literal?": _make_answer(
        "Originalmente, foi um grande avanço jurídico civil e criminal para limitar a vingança, não para incentivá-la.",
        [
            "No direito antigo, a lei de talião garantia a proporcionalidade: a punição não poderia exceder o dano causado. Funcionava como uma diretriz para os juízes, muitas vezes resolvida com compensações financeiras justas.",
            "Antes disso, no mundo antigo, uma ofensa pequena poderia gerar o extermínio de uma tribo ou família inteira por vingança desmedida.",
            "Portanto, o 'olho por olho' era uma restrição legal humanitária para a época, impedindo punições exageradas.",
            "No Novo Testamento, Jesus eleva esse princípio ético de justiça, propondo o perdão e a quebra do ciclo de retaliação."
        ],
        refs=["Êxodo 21:24", "Levítico 24:20", "Mateus 5:38-39"],
        delicate=False
    ),

    "🔍 Qual idioma Jesus falava?": _make_answer(
        "Jesus falava aramaico no seu dia a dia.",
        [
            "O aramaico era a língua comum e cotidiana da região da Galileia e Judeia no primeiro século.",
            "O hebraico era usado principalmente na liturgia, para ler as Escrituras nas sinagogas (como Jesus faz em Lucas 4).",
            "O grego era a língua comercial e oficial do Império Romano no Oriente. É provável que Jesus entendesse um pouco de grego para se comunicar com estrangeiros ou autoridades.",
            "O Novo Testamento, no entanto, foi todo escrito em Grego Koiné para que a mensagem pudesse se espalhar por todo o império romano."
        ],
        refs=["Marcos 5:41", "Marcos 15:34"],
        delicate=False
    ),

    "🔍 Quem dividiu a Bíblia em capítulos e versículos?": _make_answer(
        "A Bíblia original não tinha capítulos, versículos, nem mesmo pontuação!",
        [
            "Os manuscritos originais foram escritos de forma contínua, sem separação de palavras em alguns casos (para economizar pergaminho).",
            "A divisão em Capítulos foi feita pelo arcebispo Stephen Langton, por volta do ano 1227.",
            "A divisão em Versículos foi feita pelo impressor francês Robert Estienne, em 1551 para o Novo Testamento, e 1555 para a Bíblia toda.",
            "Essas divisões ajudam muito na localização dos textos, mas às vezes cortam o raciocínio de uma carta no meio da ideia. Por isso é sempre bom ler o contexto todo!"
        ],
        refs=[],
        delicate=False
    ),

    # --- AJUDA ---
    "Como lidar com culpa e medo por causa da religião?": _make_answer(
        "Culpa e medo podem ser fruto de trauma religioso; o caminho cristão não é terror, é graça.",
        [
            "Repare nos frutos: se uma leitura gera desespero, auto-ódio e isolamento, isso precisa ser revisto à luz do evangelho.",
            "Procure espaços seguros: comunidade inclusiva, pastoral acolhedora e/ou terapia afirmativa.",
            "Se houver risco de autoagressão, procure ajuda imediatamente com pessoas de confiança e serviços locais."
        ],
        refs=["Mateus 11:28-30", "1 João 4:18"],
        delicate=True
    ),

    "Como responder com amor quando alguém usa a Bíblia para ferir?": _make_answer(
        "Você pode responder com firmeza e mansidão: Bíblia não é arma; é caminho de vida.",
        [
            "Defina limites: 'Eu não aceito ser desumanizado(a) em nome da fé.'",
            "Traga contexto: muitas passagens tratam de violência e exploração; não de amor fiel e consentido.",
            "Se a conversa não for segura, saia: sua saúde espiritual e emocional importa."
        ],
        refs=["Mateus 7:16-20", "Efésios 4:15"],
        delicate=True
    ),

    "Precisa de ajuda contra homofobia? (Denúncias e direitos)": _make_answer(
        "Você tem direitos - e pode denunciar com segurança.",
        [
            "Se estiver em perigo imediato: ligue 190 (Polícia).",
            "Você pode registrar Boletim de Ocorrência. Guarde provas: prints, links, nomes, datas, testemunhas e laudos.",
            "O Disque 100 (Direitos Humanos) funciona 24h, aceita denúncia anônima.",
            "No Brasil, o STF enquadrou homofobia e transfobia como crimes de racismo."
        ],
        refs=["Provérbios 31:8-9"],
        delicate=True
    ) + _make_links_block([
        ("Disque 100 - Denunciar (GOV.BR)", LINKS_UTEIS["disque_100"]),
        ("SaferNet - Denúncias de violações na internet", LINKS_UTEIS["safernet_denuncie"]),
    ]),

    "Precisa de ajuda espiritual? (Igrejas inclusivas)": _make_answer(
        "Busque um lugar seguro para a sua fé - sem medo, sem coerção, sem violência.",
        [
            "Procure igrejas e comunidades cristãs inclusivas.",
            "Sinais de segurança: acolhimento explícito, linguagem respeitosa, e ausência de 'terapias de conversão'.",
            "Se você sofreu abuso espiritual, considere acompanhamento pastoral inclusivo e terapia."
        ],
        refs=["Mateus 11:28-30", "Isaías 42:3"],
        delicate=True
    ),

    "Precisa de ajuda psicológica agora? (CVV e clínicas-escola)": _make_answer(
        "Se você precisa conversar agora, você não está sozinho(a).",
        [
            "Em crise emocional, risco de autoagressão: ligue 188 (CVV) - atendimento 24h, gratuito e sigiloso.",
            "Se houver risco imediato à sua segurança: procure emergência local ou peça ajuda a alguém de confiança.",
            "Muitas faculdades de Psicologia oferecem clínicas-escola com acompanhamento a baixo custo/gratuito."
        ],
        refs=["Salmo 34:18"],
        delicate=True
    ) + _make_links_block([
        ("CVV - Centro de Valorização da Vida (188, 24h)", LINKS_UTEIS["cvv"]),
    ]),

    "O que significa 'Deus não faz acepção de pessoas'?": _make_answer(
        "É um princípio de inclusão: Deus não discrimina; Deus acolhe e chama à justiça.",
        [
            "Em Atos 10, a frase rompe barreiras religiosas e culturais: Deus acolhe quem era excluído.",
            "O critério não é marcador social, mas coração, fé, justiça e vida no Espírito.",
            "Isso sustenta uma teologia inclusiva que recusa discriminação contra pessoas LGBTQIA+."
        ],
        refs=["Atos 10:34-35", "Tiago 2:1-9", "Gálatas 3:28"],
        delicate=False
    ),
}

@app.route("/about", methods=["GET"])
def about():
    vod = fetch_verse_of_day()
    return render_template(
        "about.html",
        app_name=APP_NAME,
        footer_verse=FOOTER_VERSE,
        footer_verse_url=FOOTER_VERSE_URL,
        verse_of_day=vod,
        links_uteis=LINKS_UTEIS
    )

# =====================================================
# ROTAS
# =====================================================
@app.route("/", methods=["GET"])
def index():
    q = (request.args.get("q") or "").strip()
    selected = (request.args.get("selected") or "").strip()

    selected_norm = _normalize_key(selected)
    q_norm = _normalize_key(q)

    answer_html = ""
    display_question = ""

    if selected:
        display_question = selected
        answer_html = RESPOSTAS_DB.get(selected) or RESPOSTAS_DB.get(selected_norm) or ""

        if answer_html:
            log_question(selected)
        else:
            answer_html = _make_answer(
                "Resposta ainda não cadastrada",
                [
                    "Não encontrei uma resposta para esta pergunta no banco do app.",
                    "Isso pode acontecer por diferenças de pontuação/traço no título.",
                    "Se você me enviar o título exato que apareceu, eu cadastro a resposta no mesmo estilo."
                ],
                delicate=False
            )

    elif q:
        candidates = []
        q_lower = q_norm.lower()

        for k in RESPOSTAS_DB.keys():
            if q_lower in _normalize_key(k).lower():
                candidates.append(k)

        if not candidates:
            words = [w for w in q_lower.split() if len(w) >= 3]
            for k in RESPOSTAS_DB.keys():
                kl = _normalize_key(k).lower()
                if any(w in kl for w in words):
                    candidates.append(k)

        if candidates:
            display_question = candidates[0]
            answer_html = RESPOSTAS_DB[candidates[0]]
            log_question(display_question)
        else:
            display_question = q
            answer_html = _make_answer(
                "Ainda não tenho uma resposta pronta para essa pergunta.",
                [
                    "Escolha uma das perguntas rápidas ao lado.",
                    "Se você me enviar as perguntas que quer cobrir, eu monto novas respostas no mesmo estilo."
                ],
                delicate=False
            )

    return render_template(
        "index.html",
        app_name=APP_NAME,
        footer_verse=FOOTER_VERSE,
        quick_questions=QUICK_QUESTIONS,
        display_question=display_question,
        answer_html=answer_html,
        q=q,
        links_uteis=LINKS_UTEIS
    )

@app.route("/api/answer", methods=["POST"])
def api_answer():
    data = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"ok": False, "error": "question is required"}), 400

    q_norm = _normalize_key(question)

    if question in RESPOSTAS_DB:
        log_question(question)
        return jsonify({"ok": True, "question": question, "answer_html": RESPOSTAS_DB[question]})

    if q_norm in RESPOSTAS_DB:
        log_question(q_norm)
        return jsonify({"ok": True, "question": q_norm, "answer_html": RESPOSTAS_DB[q_norm]})

    ql = q_norm.lower()
    best = None
    for k in RESPOSTAS_DB.keys():
        if ql in _normalize_key(k).lower():
            best = k
            break

    if best:
        log_question(best)
        return jsonify({"ok": True, "question": best, "answer_html": RESPOSTAS_DB[best]})

    return jsonify({
        "ok": True,
        "question": question,
        "answer_html": _make_answer(
            "Sem resposta exata encontrada.",
            ["Tente uma pergunta rápida do menu."],
            delicate=False
        )
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
