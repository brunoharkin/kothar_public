import express from 'express';
import { chromium, Browser, BrowserContext, Page } from 'playwright';

const app = express();
app.use(express.json());

let browser: Browser | null = null;
let context: BrowserContext | null = null;
let page: Page | null = null;

// Mapa de referências para a Árvore de Acessibilidade
let refsMap = new Map<string, any>();

async function getPage() {
  if (!browser) {
    browser = await chromium.launch({ headless: true });
    context = await browser.newContext();
    page = await context.newPage();
  }
  return page;
}

app.post('/goto', async (req, res) => {
  try {
    const { url } = req.body;
    const p = await getPage();
    await p!.goto(url, { waitUntil: 'networkidle' });
    res.json({ success: true, url });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/snapshot', async (req, res) => {
  try {
    const p = await getPage();
    const snapshot = await p!.accessibility.snapshot();
    
    // Limpar refs antigas
    refsMap.clear();
    let refCounter = 1;

    // Função simples de parse (achatar a árvore para gerar as referências @eX)
    const flattenTree = (node: any) => {
      if (node.role && node.name) {
        const ref = `@e${refCounter++}`;
        refsMap.set(ref, { role: node.role, name: node.name });
        node.ref = ref; // anota na árvore retornada
      }
      if (node.children) {
        node.children.forEach(flattenTree);
      }
    };

    if (snapshot) flattenTree(snapshot);

    res.json({ success: true, tree: snapshot });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/click', async (req, res) => {
  try {
    const { ref } = req.body;
    const target = refsMap.get(ref);
    
    if (!target) {
      return res.status(404).json({ error: `Ref ${ref} not found. Run /snapshot first.` });
    }

    const p = await getPage();
    // Usa locators baseados no snapshot de acessibilidade
    const locator = p!.getByRole(target.role, { name: target.name }).first();
    await locator.click();
    
    res.json({ success: true, clicked: ref });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

const PORT = 8006;
app.listen(PORT, () => {
  console.log(`Kothar Browser Daemon running on port ${PORT}`);
});
