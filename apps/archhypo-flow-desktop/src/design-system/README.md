# Design system do desktop

- `tokens.css`: paleta clara e escura, cores semânticas, tipografia, espaçamento e dimensões compartilhadas.
- `components/`: componentes visuais reutilizáveis, sem dependência de projetos, conversas ou agentes.
- `index.ts`: entrada pública para importar os componentes.

Use tokens semânticos em vez de declarar novas cores na tela. Reserve verde, âmbar e vermelho para status acompanhados de texto. Para navegação, reutilize `NavigationButton`: ele mantém tamanho, ícone, rótulo acessível e estados de seleção e foco consistentes.

As telas continuam responsáveis pelo layout e pelo comportamento de domínio. Migre outros controles compartilhados conforme forem revisados, sem duplicar componentes do CopilotKit.

Use **Geist Variable** para interface e leitura e **Geist Mono Variable** para código e identificadores técnicos. As duas famílias são empacotadas no aplicativo. O componente `Switch` compartilha o mesmo estilo em todas as configurações e respeita a preferência de movimento reduzido.

Use `--ds-control-radius` para controles, `--ds-surface-radius` para superfícies
menores (menus, cards e compositor) e `--ds-workspace-radius` para o painel
principal e diálogos. Em janelas estreitas, o painel principal ocupa o espaço
até a borda; não empilhe molduras ou sombras para reproduzir essa separação.
