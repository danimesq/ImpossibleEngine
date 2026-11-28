Pensou por 47s

PERLA, VOCÊ TEM TODA A RAZÃO. 😭💜 Eu misturei duas camadas que precisam ficar rigorosamente separadas.

Não vamos implementar o Phonemon na ImpossibleEngine. Vamos implementar as capacidades do editor e da engine que permitiriam reconstruir o Phonemon, sem que a ImpossibleEngine sequer saiba que ele existe.

E quero estabelecer uma regra de arquitetura ainda mais forte:

> A ImpossibleEngine não terá conhecimento de quais jogos usamos como referência. Ela conhecerá apenas conceitos universais: objetos, propriedades, comportamentos, eventos, ações, condições, expressões, animações, efeitos, recursos e plataformas.

Nada de:

* `PhonemonPlugin`;

* `FlappyCompatibility`;

* `CreatureCollection`;

* `PhonemonReconstruction`;

* nomes de jogos em exemplos, fixtures ou comentários do código-fonte;

* um `.ieproj` para cada jogo que usamos como referência.

Não estamos construindo uma coleção de ports. Estamos construindo uma engine capaz de comportar todos eles.

### 🧭 1. O que estamos realmente construindo

A referência principal é a arquitetura do Construct 2, enriquecida com os avanços de extensibilidade do Construct 3.

A documentação oficial confirma uma distinção essencial:

* Plugins: introduzem tipos de objetos e seus próprios recursos.

* Behaviors: adicionam capacidades aos objetos existentes.

* Effects: acrescentam processamento visual.

* ACEs: são Actions, Conditions e Expressions, as operações disponíveis nos Event Sheets.

Essa separação também aparece no SDK do Construct 3. construct.net +2

E a nossa Impossible precisa ter isso tudo como uma arquitetura integrada, não como uma coleção de funcionalidades isoladas.

### 2\. Primeiro: o que já temos no repositório

Consultei os documentos e o catálogo atual de `danimesq/ImpossibleEngine`.

### 114

Add-ons catalogados atualmente

### 40

Plugins

### 31

Behaviors

### 43

Effects

### 640

ACEs declarados

### 204

Conditions

### 282

Actions

### 154

Expressions

Specification only

Os 114 add-ons ainda estão declarados como especificações, sem implementação efetiva no runtime.

Isso é uma distinção importantíssima: já temos um catálogo considerável, mas não temos 640 operações executáveis.

O roadmap atual também registra que existe um `impossible-runtime` com primitivas iniciais de relógio, espera, RNG determinístico e validação de bindings de eventos. Ainda falta o scheduler genérico, o IR universal e a execução integral dos ACEs.

Fontes internas do projeto:

* [ADDON-SYSTEM.md](https://github.com/danimesq/ImpossibleEngine/blob/main/docs/ADDON-SYSTEM.md?utm_source=chatgpt.com)

* [RUNTIME-IMPLEMENTATION-ROADMAP.md](https://github.com/danimesq/ImpossibleEngine/blob/main/docs/RUNTIME-IMPLEMENTATION-ROADMAP.md?utm_source=chatgpt.com)

* [PROJECT-FORMAT.md](https://github.com/danimesq/ImpossibleEngine/blob/main/docs/PROJECT-FORMAT.md?utm_source=chatgpt.com)

* [EVENT-SHEETS-JSON-TO-RUST.md](https://github.com/danimesq/ImpossibleEngine/blob/main/docs/EVENT-SHEETS-JSON-TO-RUST.md?utm_source=chatgpt.com)

Minha avaliação: a direção está correta, mas o catálogo precisa ser confrontado com uma matriz de compatibilidade real, e cada declaração precisa ganhar implementação, integração com o editor e testes.

### 3\. O pente-fino: capacidades que precisamos implementar

Vou dividir por subsistemas. A regra é que cada capacidade seja genérica, configurável, extensível e utilizável pelo editor, pelo compilador e pelo runtime.

### A. Project System

Fundação obrigatória

O formato nativo já definido é `project.ieproj`, um índice JSON para um projeto organizado em diretórios.

Precisamos suportar:

| Capacidade             | Requisito                                       |
| ---------------------- | ----------------------------------------------- |
| Project metadata       | Nome, descrição, versão, autor, identificadores |
| Project configurations | Configurações independentes de build            |
| Platform profiles      | HTML5, desktop, mobile e outros destinos        |
| Object types           | Tipos de objetos reutilizáveis                  |
| Global objects         | Objetos persistentes entre layouts              |
| Families               | Agrupamentos de tipos de objetos                |
| Layouts                | Cenas e dimensões                               |
| Event Sheets           | Folhas de eventos                               |
| Includes               | Reutilização de Event Sheets                    |
| Folders                | Organização hierárquica                         |
| Assets                 | Imagens, áudio, fontes, vídeos e outros         |
| Timelines              | Animações e sequências temporais                |
| 3D models              | Modelos e recursos tridimensionais              |
| Instance IDs           | Identidade persistente                          |
| Unknown data           | Preservação de campos desconhecidos             |

Também precisamos de:

* versionamento de formato;

* migrações;

* referências cruzadas;

* validação de integridade;

* serialização sem perda de informações;

* importação e exportação;

* referências relativas aos assets;

* overrides por configuração;

* dependências de add-ons.

Um projeto precisa sobreviver à abertura e ao salvamento sem perder propriedades que a versão atual do editor ainda não compreende.

### B. Object System

Fundação obrigatória

Esse é um dos pontos mais importantes.

Um objeto não pode ser apenas um Sprite. Ele precisa ser uma entidade extensível.

Object Type:

* Identificador e nome.

* Plugin responsável.

* Propriedades do tipo.

* Variáveis de instância.

* Behaviors anexados.

* Effects anexados.

* Animações.

* Recursos e dependências.

* Condições, ações e expressões fornecidas pelo plugin.

Object Instance:

* UID persistente.

* Posição X/Y/Z.

* Largura, altura e profundidade.

* Ângulo.

* Opacidade.

* Hotspot/origin.

* Layer.

* Visibilidade.

* Z-order.

* Frame e animação inicial.

* Variáveis individuais.

* Estado dos behaviors.

* Estado dos effects.

* Geometria de colisão.

Instancing:

* Criar e destruir objetos.

* Clonar configurações.

* Criar em posição relativa a outros objetos.

* Instâncias múltiplas do mesmo tipo.

* Seleção de instâncias.

* Iteração sobre instâncias.

* Containers e relacionamentos entre objetos.

* Objetos globais e persistência entre layouts.

E, principalmente, precisamos de um sistema correto de object picking.

No modelo do Construct 2, condições filtram instâncias e as ações são executadas sobre as instâncias selecionadas. Isso é fundamental para reproduzir o comportamento dos Event Sheets. construct-static.com +1

Não basta executar uma ação sobre todos os objetos de um determinado tipo.

### C. Plugin Architecture

Prioridade máxima

Aqui entra uma das maiores partes do nosso trabalho.

Um plugin precisa ser capaz de declarar:

* ID estável e namespace.

* Nome, versão e autor.

* Descrição e documentação.

* Ícone.

* Categoria de seleção.

* Tipo de objeto ou serviço.

* Propriedades.

* Condições.

* Ações.

* Expressões.

* Categorias próprias de ACE.

* Dependências.

* Capacidades fornecidas.

* Requisitos de runtime.

* Compatibilidade com plataformas.

* Estado de disponibilidade.

* Migrações entre versões.

E cada ACE precisa ter seu próprio contrato tipado.

Por exemplo:

Exemplo conceitual de plugin

Generic

![Blue clock icon in modern minimalist style.](https://images.openai.com/static-rsc-4/FNVjo-wBuNpdi9lbAHPIPG_rhEna_uTYLXMYDDFSmUcvM5O9mWDVbHzjFjz-7qdhETvT5L2nmegULZjLAT_11cC3T0ty0h2561Y9LqhX8k_bGsRlzszV8KAAt4nnx7AOhb0avRP3W-HU9LDnQG85VMa2vI7Lea0B2D7Pzi0_nA3WCO2TpgRyfD_VWWTgmWE4?purpose=fullsize)

Clock

Categoria: General

Conditions

* On hour changed

* On minute changed

* Compare current hour

Actions

* Set timezone

* Pause clock

* Resume clock

Expressions

* Hour

* Minute

* Second

* Timestamp

* Year

* Month

* Day

    Exemplo ilustrativo de organização, não inventário de ACEs já implementados.

Precisamos preservar IDs para sempre depois de publicados. Uma operação descontinuada deve ser marcada como deprecated, não simplesmente apagada.

Isso também é uma recomendação explícita da documentação do SDK moderno. Addon SDK +1

### D. ACE Selector

Prioridade máxima

Não podemos ter um seletor simplificado que só lista operações por nome.

Precisamos reproduzir a experiência de seleção contextual:

Ao adicionar uma Condition:

* Escolher o objeto.

* Escolher a categoria.

* Selecionar a condição.

* Preencher parâmetros.

* Configurar inversão, quando permitida.

* Confirmar.

Ao adicionar uma Action:

* Escolher o objeto.

* Escolher a categoria.

* Selecionar a ação.

* Preencher os parâmetros.

* Configurar seus valores e expressões.

* Confirmar.

Ao inserir uma Expression:

* Busca contextual.

* Categorias.

* Autocomplete.

* Assinatura dos parâmetros.

* Tipagem.

* Documentação.

* Validação.

* Inserção na posição do cursor.

E precisamos de:

* Ícones dos objetos e plugins.

* Ícones individuais dos add-ons.

* Categorias próprias para cada plugin.

* Categorias próprias para behaviors.

* Categorias de ACE separadas.

* Busca textual.

* Favoritos.

* Histórico.

* Operações destacadas.

* Operações deprecated.

* Traduções.

* Tooltips e ajuda contextual.

Uma observação importante: categoria do plugin e categoria do ACE não são a mesma coisa.

Por exemplo, um objeto pode estar na categoria Input, enquanto suas ações estão agrupadas em categorias como Buttons, Keyboard ou Device State.

A nossa arquitetura já documenta essa distinção. Agora precisamos garantir que a interface realmente a implemente.

### E. Event Sheet System

O coração da ImpossibleEngine

Aqui não podemos economizar.

O Event Sheet precisa suportar:

| Recurso            | Comportamento             |
| ------------------ | ------------------------- |
| Conditions         | Filtragem e avaliação     |
| Actions            | Execução ordenada         |
| Expressions        | Avaliação tipada          |
| Sub-events         | Eventos aninhados         |
| Event groups       | Agrupamento               |
| Include sheets     | Inclusão de outras folhas |
| Else               | Ramificação alternativa   |
| OR blocks          | Alternativas lógicas      |
| Invert conditions  | Negação                   |
| Trigger conditions | Execução por eventos      |
| Loop conditions    | Repetições                |
| For loops          | Iterações numéricas       |
| For each           | Iteração de instâncias    |
| While              | Repetição condicional     |
| Wait               | Suspensão e continuação   |
| Comments           | Documentação inline       |
| Local variables    | Escopo local              |
| Global variables   | Escopo global             |
| Event variables    | Escopo de evento          |
| Disabled events    | Desativação sem exclusão  |
| Break/continue     | Controle de fluxo         |
| Functions          | Chamadas reutilizáveis    |

Também precisamos de:

* Ordenação original dos eventos.

* Grupos colapsáveis.

* Grupos ativáveis/desativáveis.

* Condições e ações em múltiplas linhas.

* Seleção e edição múltipla.

* Copiar e colar eventos.

* Duplicação.

* Desfazer/refazer.

* Comentários associados aos eventos.

* SIDs ou IDs persistentes.

* Source mapping.

* Diagnósticos por evento.

* Busca de referências.

* Navegação entre objetos e eventos.

Uma decisão arquitetural fundamental: o Event Sheet não será simplesmente convertido em uma sequência de `if` no Rust.

Precisamos de um scheduler que compreenda:

* Ordem de execução.

* Escopo.

* Seleção de objetos.

* Contexto de triggers.

* Continuação após Wait.

* Loops.

* Reentrada de eventos.

* Eventos assíncronos.

* Ciclo de vida dos objetos.

O IR tipado precisa representar esses conceitos explicitamente.

### F. Expression Engine

Obrigatório

O motor de expressões deve ser independente da interface e capaz de funcionar tanto no editor quanto no compilador.

Suporte necessário:

* Operações aritméticas.

* Comparações.

* Operadores booleanos.

* Strings.

* Concatenação.

* Conversões.

* Funções matemáticas.

* Funções trigonométricas.

* Funções aleatórias.

* Acesso a variáveis.

* Acesso às propriedades dos objetos.

* Expressões de plugins.

* Expressões de behaviors.

* Expressões de efeitos quando aplicáveis.

* Expressões aninhadas.

* Vetores e cores.

* Funções personalizadas.

* Tratamento de erros.

* Tipagem estática.

* Validação de parâmetros.

Precisamos de autocomplete, parênteses balanceados, destaque de sintaxe e mensagens de erro na posição exata.

E nada de permitir que uma Expression aparentemente pura faça uma requisição HTTP escondida.

### G. Behavior Architecture

Prioridade máxima

Behaviors são extensões anexáveis aos tipos de objetos.

A mesma arquitetura deve permitir que um objeto receba múltiplos behaviors, cada qual com suas propriedades, ACEs e estado por instância.

O catálogo atual já contempla 31 behaviors.

Mas precisamos organizar a implementação em sistemas compartilhados:

* Movement & Steering.

* Physics & Collision.

* Camera & World Bounds.

* Animation & Timeline.

* AI & Navigation.

* Input & Interaction.

Cada behavior precisa declarar:

* Propriedades iniciais.

* Propriedades editáveis.

* Estado por instância.

* Condições.

* Ações.

* Expressões.

* Ordem e fase de atualização.

* Dependências.

* Compatibilidade.

* Requisitos de runtime.

E atenção: behaviors não devem ser obrigatoriamente um crate Rust cada. O sistema deve compartilhar infraestrutura e permitir implementação individual.

### H. Effects Architecture

Prioridade alta

O catálogo já possui 43 efeitos declarados.

Precisamos de um pipeline de efeitos compartilhado pelo renderer.

Recursos obrigatórios:

* Efeitos por objeto.

* Efeitos por layer.

* Pilhas de efeitos.

* Ordem configurável.

* Parâmetros editáveis.

* Valores animáveis.

* Ativação/desativação.

* Blend modes.

* Alpha handling.

* Render graph.

* Shader compilation.

* GLSL.

* WGSL.

* Background sampling.

* Depth sampling.

* Cross-sampling.

* Compatibilidade por renderer.

* Diagnósticos para efeitos indisponíveis.

Não quero um efeito que simplesmente desapareça em um target que não o suporta.

A engine precisa informar a incompatibilidade, oferecer uma implementação alternativa explicitamente identificada quando existir, ou impedir aquele build conforme a política de compatibilidade.

### I. Animation System

Precisamos contemplar tanto animações 2D quanto sistemas temporais genéricos.

* Spritesheets.

* Animações com múltiplos frames.

* Duração individual dos frames.

* Loop.

* Ping-pong.

* Repeat count.

* Repeat-to.

* Velocidade.

* Hotspots.

* Collision polygons por frame.

* Estados de animação.

* Transições.

* Eventos de início e término.

* Pausa e retomada.

* Mudança de frame.

* Timeline.

* Interpolação.

* Easing.

* Tween.

* Animação de propriedades.

* Sequenciamento.

* Sincronização.

O sistema precisa permitir que animações sejam controladas tanto por ações quanto por behaviors e timelines.

### J. Layout & Layer System

Não basta desenhar uma cena.

Precisamos de:

* Layers.

* Ordem e profundidade.

* Parallax X/Y.

* Opacidade.

* Visibilidade.

* Background color.

* Transparência.

* Zoom rate.

* Scrolling.

* Viewport.

* Câmeras.

* Unbounded scrolling.

* Layout transitions.

* Layout inicial.

* Layout persistente.

* Instâncias globais.

* Objetos persistentes.

* Dimensões configuráveis.

* Orientação.

* Resolução lógica.

* Scaling modes.

* DPI.

* Fullscreen.

* Letterboxing.

Cada layout também precisa ter propriedades independentes e referências às suas Event Sheets.

### K. Input System

Um sistema universal de entrada:

* Keyboard.

* Mouse.

* Touch.

* Multi-touch.

* Gamepad.

* Joystick.

* Multiple controllers.

* Input mapping.

* Rebinding.

* Deadzones.

* Analog axes.

* Buttons.

* Gestures.

* Pointer position.

* Pointer coordinates.

* Wheel.

* Focus.

* Input simulation.

Uma abstração importante: separar o dispositivo físico da ação semântica.

Isso permite que uma mesma operação funcione com teclado, touchscreen ou gamepad sem duplicar toda a lógica.

### L. Host & Platform Plugins

Aqui entram as funcionalidades que dependem do ambiente de execução.

* Browser.

* HTTP.

* WebSocket.

* Multiplayer.

* Storage.

* File System.

* Clipboard.

* Fullscreen.

* Browser navigation.

* User Media.

* Camera.

* Microphone.

* Video.

* Audio.

* Notifications.

* Haptics.

* Text to Speech.

* Platform identity.

* Device information.

* Social integrations.

* Advertising.

* Platform-specific services.

Essas capacidades precisam de adapters, não de chamadas arbitrárias espalhadas pelo runtime.

E multiplayer deve ser separado em:

* Transport.

* Signalling.

* Sessions.

* Rooms.

* Peers.

* Authority.

* Input replication.

* State replication.

* Interpolation.

* Reconnection.

Um WebSocket sozinho não é um sistema multiplayer.

### 4\. O que o Phonemon exige da engine, sem implementar nada específico dele?

Agora sim, vamos aplicar o pente-fino ao projeto original.

O arquivo de metadados declara nove plugins e três behaviors. Isso permite construir uma matriz de compatibilidade objetiva.

| Recurso encontrado na fonte | Capacidade genérica necessária        |
| --------------------------- | ------------------------------------- |
| Sprite                      | Plugin de objetos visuais 2D          |
| Tiled Background            | Textura repetida e renderização tiled |
| Text                        | Renderização de texto                 |
| TextBox                     | Controles editáveis de texto          |
| Button                      | Controles interativos                 |
| Touch                       | Entrada touchscreen                   |
| Clock                       | Relógio e expressões temporais        |
| WebSocket                   | Comunicação de rede                   |
| Multiplayer                 | Sessões e sincronização               |
| Platform                    | Movimento e física de plataforma      |
| Scroll To                   | Câmera seguindo objetos               |
| Solid                       | Colisões e superfícies sólidas        |

Nenhum desses nomes precisa ser associado ao projeto de origem dentro do código. São capacidades genéricas.

### O que isso significa tecnicamente?

1\. Sprite

Precisamos suportar:

* Múltiplas animações.

* Frames.

* Hotspots.

* Collision polygons.

* Alteração de animação.

* Alteração de frame.

* Opacidade.

* Transformações.

* Condições de animação.

* Eventos de término.

2\. Tiled Background

Precisamos de:

* Texturas repetíveis.

* Escala.

* Offset.

* Repetição independente dos limites da imagem.

* Transformações.

* Renderização por layer.

3\. Text e TextBox

Precisamos de dois tipos distintos de objetos:

* Texto renderizado, com fontes, alinhamento, wrapping, line-height e cor.

* Campo editável, com foco, placeholder, tipo de entrada, leitura/escrita, teclado virtual e eventos de alteração.

4\. Button

Precisamos de:

* Estados normal, hover, pressed e disabled.

* Eventos de clique.

* Habilitar/desabilitar.

* Foco.

* Acessibilidade.

* Integração com teclado e touchscreen.

5\. Touch

Precisamos de:

* Touch start.

* Touch end.

* Touch cancel.

* Identificadores individuais.

* Coordenadas.

* Múltiplos dedos.

* Conversão entre coordenadas de tela e mundo.

6\. Clock

Precisamos de:

* Hora.

* Minuto.

* Segundo.

* Data.

* Timestamp.

* Fuso horário.

* Relógio real.

* Relógio simulado.

* Eventos de alteração temporal.

Não devemos confundir relógio real com o relógio da simulação.

7\. WebSocket

Precisamos de:

* Conectar.

* Desconectar.

* Enviar mensagens.

* Receber mensagens.

* Estados de conexão.

* Erros.

* Eventos assíncronos.

* Reconexão.

* Configuração de protocolos.

8\. Multiplayer

Precisamos da arquitetura de sessões descrita anteriormente, incluindo descoberta, identidade, autoridade e sincronização.

9\. Platform Movement

Precisamos de:

* Gravidade.

* Velocidade horizontal e vertical.

* Pulo.

* Aceleração.

* Desaceleração.

* Fricção.

* Colisão com chão e teto.

* Inclinações.

* Plataformas móveis.

* Detecção de chão.

* Controles simulados.

* Configuração de movimento.

10\. Scroll To

Precisamos de:

* Câmera seguindo uma instância.

* Alvos dinâmicos.

* Suavização.

* Deadzone.

* Limites.

* Offset.

* Efeitos de câmera.

11\. Solid

Precisamos de:

* Colisores.

* Superfícies sólidas.

* Resolução de colisão.

* Colisão entre tipos diferentes.

* Colisão por geometria.

* Ativação e desativação.

* Interação com behaviors de movimento.

Percebe a diferença?

Não estamos criando um sistema de personagens, login ou criaturas. Estamos implementando os tipos de objetos e comportamentos universais que permitem que um projeto qualquer construa essas experiências.

### 5\. Ribbon e interface completa do editor

Quero incluir isso expressamente no escopo, porque a Impossible não pode ser apenas um compilador com uma GUI improvisada.

Parte do produto

![The Construct 2 Interface - Construct 2 Documentation](https://images.openai.com/static-rsc-4/4vQBzC9VaXAMTfGaAFRPNmGj4fmPimA51T6YJ6BKoc1ITpwxB-A31WcjYiTsIGpuHrCdTxHwSH2hDv-9iNHJFfaXf8G44NWqqtGXF4W3HgEcUYuzloPVG0XrTLjN6FC6IlGxpY1w3RttY4BFQBMxipsi_LcMj0YeU2tLEZ0BIQt8am2KNCKYbW2BG4Dufogs?purpose=fullsize)

![How to set random frame on spawn? - Game Makers Help](https://images.openai.com/static-rsc-4/7b4yjMpGJD9WCYWsZy8fsi-U-72f7WK-fXX4_aI6tUPXn0rcn_EIm4aEY2zQJ8eQDHdbRvkdVfKIG-XrtuP90jeRAfLn7uZrBDhSEyk5P_ripimSl8cwE7H4Tup_qzDVgbSGrd8Nqa_QU7zaFsACQMX-BvFAA3rKLoENHXutX9FmNAIalAII2qlGgCO6lMAp?purpose=fullsize)

![Construct's interface - Construct 3 Documentation](https://images.openai.com/static-rsc-4/V0qnCI8JWAQO2KQb16aQxZtLm_CJF9Xe1hcXWcyJapEGVa8mEahxBKAwLSG_h7TKH9oS48DKCD7h4CmjZwozrLYh6pfr-KwxMmEPAKCWOPQzk87Z7VBuQa_4qB_gcO2Xm2YjbyKco3B6sqbW0eay0uq8hXIjVXEQ9eOqAKDPzepbMtz1hEpnGOvJMiEot8FS?purpose=fullsize)

![10 Best 2D game engines for creating simple multiplayer webapps as of 2026 - Slant](https://images.openai.com/static-rsc-4/lopZSPgZ-YXrQNOlL9vWnnmA5SmlCezFs0dLHWin8X-adrvy9Om7763Tzy0UokLgOAiHJiWFyZ4eP8vt5rcvs7KQ0BBLr1QY553z3i9qav1O1hqYgxH3YZqYO2oU_zkRPQO-7bOb1VPk3UgFDq9kIVaqgL7_oR4mhLVjpH1sp4DTwemzr1l2uHgkHzGVc97K?purpose=fullsize)

![Set angle toward position - Game Building Help](https://images.openai.com/static-rsc-4/RiregE3Jf3NSNUgIH8cHqLZsSSKK2Z4BrfNjLdTBMBMtQcFqirzwsHb5eq-8BcGJiUdZqoVXidVLTIfDWNGk1U26Ed6s4gbaLcXcR19f-ikamO5MJa9Chgf6qOT1dkmBHBUhVj6HVFKLy_nlmwxV7hlp1joCshgdZ94dB17goanaQ2qMCRa6sGsSn8sYqyXo?purpose=fullsize)

![Image 3 - Construct 3 - IndieDB](https://images.openai.com/static-rsc-4/Oc59qVbHPlqO6L24p3WGGTSDwTPCZLFM8-B2JST80LdC-mASr8kmJEdGCwsK_8oMdh0p3OEQucWJ1-szFO1qCT6Ch-UTwn6g8JSfb8BV2fdOPwLO0txtaVrDCLJPV5iZ2CvcKKlc7f160A5c4_jZOCMYteL36ls8fnsUx0ldbVarzRj46ZS_scQ1qh03MjFg?purpose=fullsize)

![Anleitung für Anfänger in Construct 2 - Free Tutorial](https://images.openai.com/static-rsc-4/yd3LoUD7_I83v1c2pR7pfVdlOsJ2z7ROWov9ukQKIx1xXpV2h9M3JzEkDiXJrAZlN15hGg9vhwcbihV-PLmIJm3kErUxfwwcZwnT2cGfdL96iDF8lPYg8hhhFjJTK1EcrVcUHzgNK1758KjScnonLl59S1OOHs0floq-WzLC2zE5Um25-SR6kvVrskKXTjlW?purpose=fullsize)

![Importing Sound To Game Using Construct 2](https://images.openai.com/static-rsc-4/ExcJygCthsZwq65USgbJSX4SU8KfSXO6153UvsbZ-NqeEi5Qls1RAoIkCIh88C5Q1vOw3aHv_usj8A-mgn1qsD9se6ILmsJNFjkXGhjD3WC6AXlOUPh5DzQuvE4TSHBa5WCicP6pwS_7aDSaMrQT-HHd1S0Ik7PbSmQ9Ev0qJ6HkkJoyqIhd_8zucUpuazaD?purpose=fullsize)

![10 herramientas de creación de videojuegos para programadores principiantes](https://images.openai.com/static-rsc-4/eczdrztY3rrtGDE1tvFHc4ORP-MI9pe8RHPvAODRizFKZL_90WfBedpi8o09e8Ys2U9cBQv6paAoz8bDEuGWdWsTqb1K_yarOrKTEHi_18T6ke5hLOA-f_yjyA02T2tQoJzrV6V6xjXXV3oAXWBMAt9h_CU5Vil5n5LtTg8-Oa0WcHm5hmabcKyBKErylBao?purpose=fullsize)

![Project Creation](https://images.openai.com/static-rsc-4/ZZ3oOCD7ejpCaBd_0FZkVRP0aYaC2n6F3HgZKuPyvb18jaQB43usODBO235I8Zki90i1BIsIuxux0e6UIPPzjAPIRhF77L9lWIEkub4q1zmI3d5kty1OTVy5CUudZYzXcf8QfMga1oiOMHpyz-0kQ3ZfijsNbputJLGBv9LQOVl_28Luju7Gm6WqF8Axmnwd?purpose=fullsize)

![Flappy Bird –](https://images.openai.com/static-rsc-4/TJN1kDYzUZX47UwTYZaZIVtTkgRfGXvQ5Z7I_5S1b7UFMSA5zoWwZCqPEHKtZTpPx8r2ix8Z8HljtIhM1MlIjp-9q2JsL_EXFEVeLKrlepmHSAWJcaE_UO0u6kITH4vKmqmfN0N31AqeOkRa_uAFTwM2mFP_VZPaeJ537-bX_OGh-27kLPz4S4cLHsLrJ3vd?purpose=fullsize)

### Ribbon

A interface deve possuir:

* Title bar.

* Quick Access Toolbar.

* Save.

* Undo.

* Redo.

* Preview.

* Ribbon tabs.

* Ribbon groups.

* Large buttons.

* Small buttons.

* Dropdowns.

* Split buttons.

* Separators.

* Tooltips.

* Keyboard shortcuts.

* Collapsible ribbon.

Grupos de comandos:

| Aba    | Grupos                                              |
| ------ | --------------------------------------------------- |
| Home   | Clipboard, Undo, Selection, Configurations, Preview |
| View   | Layout, Zoom, Panels, Workspace                     |
| Events | Event insertion, Variables, Groups, Includes, Debug |

Não precisamos copiar os nomes comerciais ou os recursos externos do editor original. Precisamos reproduzir a capacidade e a ergonomia.

### Docks e painéis

Precisamos de:

* Project Bar.

* Objects Bar.

* Properties Bar.

* Layers Bar.

* Animations Editor.

* Event Sheet Editor.

* Add-on Manager.

* Asset Browser.

* Debugger.

* Search.

* Find References.

* Configuration Manager.

Os painéis precisam ser:

* Dockable.

* Undockable.

* Pinnable.

* Auto-hide.

* Closable.

* Reordenáveis.

* Restauráveis.

* Configuráveis por workspace.

### Properties Bar

Não pode ser um formulário fixo.

O painel precisa ser gerado dinamicamente conforme:

* Tipo de objeto.

* Instância selecionada.

* Behavior selecionado.

* Effect selecionado.

* Layout selecionado.

* Layer selecionado.

* Configuração ativa.

Cada add-on declara seus campos e o editor constrói os controles adequados.

Tipos de propriedades:

* Number.

* Integer.

* String.

* Boolean.

* Enum.

* Color.

* File.

* Asset.

* Object reference.

* Layer reference.

* Layout reference.

* Vector.

* Polygon.

* Font.

* Animation.

* Custom editor.

Também precisamos de propriedades agrupadas, expansíveis, ordenação, busca e validação.

### Event Sheet GUI

O editor precisa representar visualmente:

![Construct 2 for Windows - Download it from Uptodown for free](https://images.openai.com/static-rsc-4/6mX2j-31bG8_GF4PtUl4y37HxGs1M-971sKlhidDs_78dFV6hG7ZeMcJWo9upJV3nIUBA92w3RN4czaAAdW-fr1rAZ3iIPbcxtPPkvGtpukc5FpRHilLlLTbDl1sT5s3Bp8L03aYbiL3QkZ0In88XUkikNqSaQz82rD_5_8hXgAItgPjbhv0Kx5NRhhpO4hJ?purpose=fullsize)

* Gutter com números.

* Conditions à esquerda.

* Actions à direita.

* Ícones de objetos.

* Categorias.

* Nested events.

* Scope guides.

* Event groups.

* Else.

* OR blocks.

* Comments.

* Add Condition.

* Add Action.

* Drag and drop.

* Seleção múltipla.

* Edição de parâmetros.

* Context menus.

* Collapse/expand.

* Copy/paste.

* Search.

E não quero que os Event Sheets sejam apenas uma representação visual de JSON.

O modelo de dados deve ser estruturado, editável e semanticamente tipado. A GUI é uma interface para esse modelo.

### 6\. Add-on SDK: plugins, behaviors e effects próprios

Outra coisa que precisamos levar do Construct 3 é a capacidade de extensibilidade para terceiros.

O SDK moderno separa metadados, ACEs, recursos de localização, ícones, código do editor e código de runtime. Addon SDK Documentation +2

Nossa implementação deve permitir:

* Criar plugins.

* Criar behaviors.

* Criar effects.

* Declarar propriedades.

* Declarar ACEs.

* Declarar categorias.

* Registrar ícones.

* Adicionar traduções.

* Declarar dependências.

* Implementar runtime.

* Implementar integração com o editor.

* Empacotar add-ons.

* Instalar e desinstalar.

* Atualizar versões.

* Validar compatibilidade.

* Resolver dependências.

* Detectar conflitos.

* Migrar projetos.

### Uma estrutura possível

```text
addons/
├── builtin/
│   ├── plugins/
│   ├── behaviors/
│   └── effects/
│
├── third-party/
│
└── sdk/
    ├── manifests/
    ├── schemas/
    ├── localization/
    ├── editor-api/
    ├── runtime-api/
    └── packaging/
```

Não precisamos copiar a estrutura de arquivos do SDK original. Precisamos preservar as capacidades.

E uma decisão que eu considero essencial: add-ons de terceiros devem ter permissões explícitas para acessar rede, arquivos, câmera, microfone e outros recursos sensíveis. Não vamos transformar extensibilidade em execução irrestrita de código.

### 7\. O que precisa ser corrigido no catálogo atual

O catálogo atual é um bom começo, mas há algumas lacunas de produto que não podem ficar escondidas atrás da contagem de 640 ACEs.

| Área            | Estado atual           | Próximo trabalho                    |
| --------------- | ---------------------- | ----------------------------------- |
| Plugins         | 40 declarados          | Implementar e validar               |
| Behaviors       | 31 declarados          | Implementar sistemas compartilhados |
| Effects         | 43 declarados          | Renderer e shaders                  |
| ACEs            | 640 declarados         | Resolver, compilar e executar       |
| Add-on selector | Especificado           | GUI funcional                       |
| Properties Bar  | Parcialmente planejada | Editor dinâmico                     |
| Ribbon          | Referência documentada | Implementação GTK                   |
| Event Sheet GUI | Referência documentada | Editor completo                     |
| Add-on SDK      | Contratos declarados   | SDK utilizável                      |
| Runtime         | Primitivas iniciais    | Scheduler e sistemas                |
| Importer        | Estratégia documentada | Adaptadores genéricos               |
| Debugger        | Planejado              | Instrumentação real                 |

Há ainda uma diferença importante entre compatibilidade de formato e compatibilidade comportamental.

Um projeto pode ser importado sem perder seus arquivos e ainda assim funcionar incorretamente.

Por isso, precisamos de testes de conformidade para cada ACE, behavior, plugin, efeito e operação de controle de fluxo.

### 8\. A regra de anonimização: precisamos corrigir a estratégia do repositório

Aqui encontrei algo que merece atenção.

O roadmap atual ainda contém uma vertical slice identificada pelo nome de um jogo, com caminhos como:

```text
examples/flappy-madruga/
projects/flappy-ramon/
docs/GAME-IMPORT-AND-MIGRATION.md
```

Isso contraria a nova regra que você estabeleceu.

Não estou dizendo que precisamos perder o conhecimento técnico extraído desses projetos. Pelo contrário: precisamos separar o conhecimento das fontes que o originaram.

Minha proposta:

Dentro de ImpossibleEngine:

```text
ImpossibleEngine/
├── addons/
│   ├── builtin-v1.json
│   └── ...
│
├── crates/
│   ├── impossible-runtime/
│   ├── impossible-ir/
│   ├── impossible-compiler/
│   ├── impossible-project/
│   ├── impossible-renderer/
│   └── impossible-addon-sdk/
│
├── src/
│   ├── editor/
│   ├── project/
│   ├── events/
│   ├── objects/
│   ├── behaviors/
│   ├── effects/
│   └── compiler/
│
├── tests/
│   ├── conformance/
│   │   ├── events/
│   │   ├── plugins/
│   │   ├── behaviors/
│   │   ├── effects/
│   │   ├── rendering/
│   │   └── platform/
│   │
│   └── fixtures/
│       ├── object_instances/
│       ├── event_scopes/
│       ├── animation_frames/
│       └── collision_geometry/
│
└── docs/
    ├── ARCHITECTURE.md
    ├── PROJECT-FORMAT.md
    ├── ADDON-SYSTEM.md
    ├── EVENT-SHEETS.md
    ├── RUNTIME.md
    ├── EDITOR.md
    ├── RENDERER.md
    └── COMPATIBILITY.md
```

Os nomes acima são exemplos de organização, não uma ordem para criar todos esses crates imediatamente.

### Como testar sem revelar os jogos?

Utilizamos testes sintéticos e anônimos.

Por exemplo:

```text
fixture_platform_movement_001
fixture_object_picking_002
fixture_animation_loop_003
fixture_nested_events_004
fixture_websocket_async_005
fixture_multiplayer_replication_006
```

Cada fixture testa uma capacidade isolada, ou combinações de capacidades.

Os projetos originais ficam fora do código-fonte público da engine. Seus nomes, assets e estruturas específicas não entram no catálogo.

E não precisamos criar um `.ieproj` completo para cada referência. O objetivo é testar o motor universal, não manter uma coleção de jogos dentro dele.

A própria documentação deve dizer apenas que a engine busca compatibilidade com formatos e semânticas de projetos externos, sem identificar as referências utilizadas na pesquisa.

### 9\. O que significa ser fiel de verdade?

Quero estabelecer cinco níveis de compatibilidade:

| Nível         | Significado                                         |
| ------------- | --------------------------------------------------- |
| 1. Structural | Importar e preservar os dados                       |
| 2. Semantic   | Interpretar corretamente as operações               |
| 3. Behavioral | Executar com os mesmos resultados                   |
| 4. Visual     | Reproduzir renderização e animações                 |
| 5. Platform   | Reproduzir integrações e comportamento nos destinos |

Um recurso não pode ser considerado compatível simplesmente porque existe um ACE com o mesmo nome.

Por exemplo, `Wait` precisa preservar:

* O tempo de espera.

* A ordem de execução.

* O contexto do evento.

* A seleção de objetos.

* A continuação dos subeventos.

* A interação com outros eventos.

* O comportamento quando o layout muda.

O mesmo vale para colisões, animações, efeitos, triggers e multiplayer.

Nossa unidade de progresso será a equivalência funcional, não a quantidade de features declaradas.

### 10\. Ordem de implementação que recomendo

Não precisamos implementar 114 add-ons simultaneamente. Precisamos implementar as fundações que desbloqueiam todos eles.

### Roadmap consolidado

* Fundação do projeto

    Formato `.ieproj`, objetos, instâncias, layouts, layers, variáveis, assets, IDs persistentes e serialização.

    Primeira prioridade

* Add-on Registry e SDK

    Plugins, behaviors, effects, ACEs, categorias, ícones, propriedades, localização e dependências.

* Event Sheet Engine

    IR tipado, scheduler, picking, triggers, loops, waits, funções, expressões e controle de fluxo.

    Bloqueador central

* Runtime de objetos

    Ciclo de vida, transforms, animação, colisão, movimento, câmera e atualização.

* Editor completo

    Ribbon, docks, Properties Bar, Object Browser, Event Sheet GUI, Add-on Selector e Debugger.

* Renderer e Effects

    Render graph, 2D, 3D, shaders, blend modes, sampling, timelines e efeitos.

* Input e Host Services

    Keyboard, Mouse, Touch, Gamepad, HTTP, WebSocket, Storage, Audio e integrações.

* Multiplayer e extensibilidade avançada

    Sessões, sincronização, plugins externos, adapters, compatibilidade e permissões.

* Compatibilidade e publicação

    Importadores genéricos, testes diferenciais, builds nativos, WebAssembly, exportadores e documentação.

### 11\. Minha definição final de ImpossibleEngine

Quero que a gente adote este princípio como critério para todas as próximas decisões:

### Universal Project Capability

A ImpossibleEngine deve implementar as capacidades de autoria, extensão, execução e publicação necessárias para reproduzir fielmente projetos construídos em engines visuais de referência, sem depender deles, identificá-los ou incorporar suas regras específicas.

Uma engine. Um formato nativo. Um catálogo universal. Infinitas possibilidades.

E tem três decisões que considero inegociáveis:

* Nenhuma feature de jogo específico entra no runtime genérico. Se uma capacidade pode ser expressa por plugins, behaviors, effects, eventos ou módulos nativos, ela deve ser modelada nesses sistemas.

* Nenhuma referência de jogo entra na identidade pública da ImpossibleEngine. Nem nomes, nem pastas, nem comentários, nem documentação.

* Nenhuma capacidade é considerada implementada só porque está declarada no JSON. Precisa de implementação, integração com o editor, execução real e testes.

### Minha conclusão sobre o Phonemon

O projeto foi útil para identificar uma matriz de requisitos, especialmente em:

* Objetos e plugins.

* Animações e geometria.

* Controles de interface.

* Relógio.

* Comunicação.

* Multiplayer.

* Movimento.

* Câmera.

* Colisões.

* Event Sheets.

Mas não vamos adicionar absolutamente nada sobre captura de criaturas, personagens, login específico ou regras daquele jogo.

Se amanhã você decidir reconstruí-lo, a ImpossibleEngine deverá simplesmente oferecer todas as ferramentas necessárias, sem precisar saber de onde veio aquela necessidade. É exatamente essa independência que eu quero preservar.

E, Perla, acho que essa mudança de perspectiva é muito importante: não queremos uma engine que consiga portar meia dúzia de jogos conhecidos. Queremos uma engine cujas abstrações sejam suficientemente completas para que os jogos sejam consequência natural das capacidades dela. 💜
