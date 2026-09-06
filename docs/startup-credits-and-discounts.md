# Startup Credits, Free Programs, and Founder Discounts for the Hermes Agent Stack

Research date: 2026-09-05. Compiled from four parallel web-research passes over official
provider pages (search-indexed text where direct fetches were blocked) and 2026-dated
third-party guides. Every dollar figure marked **unverified** could not be confirmed against
an official page on the research date. Links were accessed 2026-09-05 unless a row says otherwise. A few rows (AngelList, Product Hunt Founder Club, Figma) have no official program page to link; those rows say so and are marked unverified.
Rows whose confidence column reads "Unverified", "Third-party", or "Semi-verified" have no primary-source
confirmation and should be treated as leads, not facts. Re-check the linked page before relying on a number.

## 1. Headline numbers

These are **nominal catalog values**: the sum of each program's published maximum. They are not
proven simultaneously eligible or stackable. Many programs exclude prior credit recipients, count
credits from other channels against their own limits, or gate on funding stage. Treat the table as a
ceiling to reconcile against your own facts, not a forecast.

| Path | Cloud + AI credits (nominal) | SaaS credits / discounts (nominal) | Notes |
|---|---|---|---|
| Bootstrapped, no investor, no accelerator | $34K | $117.5K | Cloud + AI: Azure 5 + GCP Start 2 + AWS Founders 1 (up to $5K over time) + Cloudflare Tier 3 10 + Daytona 10 + OpenRouter 5 + Neon self-funded 1 = $34K. SaaS and tooling: PostHog 50 + Retool 60 (discount value) + Sentry 5 + Stripe Atlas 2.5 (automatic for eligible companies, realized only against eligible fees) = $117.5K. Segment is excluded: its startup URL now redirects to Twilio's startups page, which states Twilio offers no additional startup credits, so no current first-party terms support the $25K. Sentry and Stripe are classified as SaaS in every scenario in this document. Excludes Anthropic, whose community tier carries no credits and whose credit tiers require institutional funding with no verified amount, and excludes Novita, whose award is reviewed on backing and mostly earned through matched spend |
| Funded or partner-backed, pre-seed to Series A, stage-coherent | $970K | $225K | Cloud + AI: Google AI tier 350 + AWS Portfolio 200 + Azure 150 (usage milestones) + Cloudflare Tier 2 100 + DigitalOcean 100 (varies by partner) + Together 15 (under $5M raised) + Vercel 30 + Modal 25 = $970K. Neon/Databricks venture-backed tier is excluded because the official program publishes only a combined "up to $200K" that depends on stage and funding, with no per-startup allocation. SaaS: Datadog 100 + PostHog 50 + Retool 60 (discount value) + GitHub 10 + Sentry 5 = $225K. Segment excluded for lack of current first-party terms. Each program appears in exactly one column. Anthropic up to $100K is unverified and excluded. Each program has its own partner list and funding test, so no single check unlocks all of these |
| Catalog ceiling across all stages, not one scenario | $1,255K (about $1.26M) | $225K | Same cloud list with the maxima that require later stages: Cloudflare Tier 1 350 instead of 100 and Together 50 instead of 15, giving 970 + 250 + 35 = $1,255K. Listed only to show the published ceiling; a single company cannot be pre-seed and over $10M raised at once |
| Payroll tax (once you run W-2 payroll) | Up to $500K per tax year, elective for at most 5 tax years | | Federal R&D credit payroll offset, IRC 41(h). Actual amount is the credit you compute on Form 6765, which is usually far below the cap |

### Confirmed directly eligible subtotal (no referral, official amount verified 2026-09-05)

This subtotal only includes programs whose current official page states the amount and whose
eligibility a bootstrapped startup can satisfy without a VC, accelerator, or partner ID. It assumes
the baseline facts every program checks: a registered company, a live website with a matching
company-domain email, founded within the last few years, no prior credits from that provider, and
no institutional funding. Confirm each row against your own facts before counting it.

| Program | Amount | Official condition that must hold |
|---|---|---|
| Microsoft for Startups, open offer | $5,000 | New Azure customer; $200 starter credit, then up to $5K after business verification (milestones 1 and 2) |
| Google for Startups Cloud Program, Start tier | $2,000 | Pre-funded, founded within the last 24 months, working MVP, planning to seek venture funding, no Google Cloud credits beyond the free trial; counts against the under-$5K prior-credit limit for Scale (https://cloud.google.com/startup/pre-funded, accessed 2026-09-05) |
| AWS Activate Founders | $1,000 | Self-serve; selected startups may receive up to $5K over time |
| Cloudflare for Startups, Tier 3 | $10,000 | Bootstrapped or self-funded and under $1M raised (program FAQ as reported by the independent review); the program page states no minimum funding is required. Payment method required; card is billed after credits are consumed or expire |
| Daytona Startup Grid | $10,000 | AI or agent product; pitch deck and 100-word story |
| OpenRouter for Startups | $5,000 | Pre-Series B, under ~$500 lifetime spend |
| Neon / Databricks, self-funded tier | $1,000 | Under $1M raised, early product development; Neon credits valid 12 months (https://neon.com/startups) |
| **Cloud + AI credits, confirmed** | **$34,000** | 5 + 2 + 1 + 10 + 10 + 5 + 1. Novita excluded: only up to $1K is upfront, the rest is earned via matched spend, and Novita reviews backing and stage. Sentry is counted under SaaS below |
| PostHog for Startups | $50,000 | Under 2 yrs old, under $5M raised |
| Sentry for Startups | $5,000 | Pre-seed to Series A; credits valid 1 year |
| **SaaS credits, confirmed** | **$55,000** | PostHog 50,000 + Sentry 5,000. Segment excluded: no current first-party terms (see section 2g). Retool's up-to-$60K is a discount on list price and is excluded. Stripe Atlas's $2,500 product credit is excluded because its realized value depends on eligible Stripe fees actually incurred within the year |

Non-cash confirmed benefits not in the totals: ElevenLabs Startup Grant (33M characters for 12
months), NVIDIA Inception and Intel Liftoff membership, Microsoft 365 via Microsoft for Startups,
and the free tiers listed in sections 2c through 2e.

Most credits expire 6–12 months after activation and are one-time per tier. Stagger activations to
match your compute ramp instead of claiming everything on day one.

## 2. Programs mapped to the tools this repo uses

### 2a. LLM and inference providers (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, and friends)

| Program | Worth | Eligibility | Referral needed? | Link | Confidence |
|---|---|---|---|---|---|
| OpenRouter for Startups | Up to $5,000 credits across 300+ models, 0% platform/BYOK fees for 12 mo; credits expire ~6 mo | Pre-Series B, under ~$500 lifetime spend, company site and email | No | https://openrouter.ai/startups | Official |
| Anthropic Startup Program (Claude for Startups) | Two distinct paths. **Community tier** (referral-free): program community access and founder resources; the official page states no credit amount for this tier, so it contributes $0 to every total here. **Credit tiers**: API credits and top rate-limit tier, available only to startups with institutional equity funding, with larger amounts by partner VC or accelerator nomination; aggregator figures ($5K, $100K, $500K for YC) are unverified and excluded | Founded < 4 yrs, no prior Anthropic startup credits. Community tier open to bootstrapped founders; any credits require the institutional path | No for community tier (no credits); yes for credit tiers | https://claude.com/programs/startups (accessed 2026-09-05) | Official page; credit amounts unverified |
| OpenAI for Startups | Free API credits (~$5K typical, unverified), tier upgrades, engineer time | Must come via partner VC/accelerator, or $1K–$2.5K via Brex/Ramp/Mercury/Microsoft perks | Yes | https://openai.com/startups/ | Official |
| OpenAI Grove | **Closed.** Applications closed January 12, 2026 for the cohort that ran January 22 to February 27, 2026. The page describes API credits, early tool access, and mentorship without a standing published amount for future cohorts. Excluded from every total in this document | Pre-idea and early builders; about 15 participants per cohort; no new cohort announced as of 2026-09-05 | n/a | https://openai.com/index/openai-grove/ (accessed 2026-09-05) | Official; inactive |
| Google for Startups Cloud Program | Start: $2K. Scale: $200K. AI-first: up to $350K over 2 yrs. Scale and Scale AI members may also request $10K of credits for partner models in Model Garden (Anthropic, Mistral, AI21) through their account executive (https://cloud.google.com/startup/perks). Covers Gemini/Vertex | Start: pre-funded, founded within the last 24 months, working MVP, planning to seek venture funding, no prior credits beyond the free trial. Scale/AI: pre-seed or seed raised within the last 5 years or Series A within the last 12 months from institutional investors, or a partner accelerator; under $5K prior GCP credits; application and Google approval required | No for Start; yes for Scale/AI | https://cloud.google.com/startup/pre-funded and https://cloud.google.com/startup/benefits (accessed 2026-09-05) | Official |
| Gemini API free tier (AI Studio) | Free Flash models, ~10–15 RPM, 250–1,500 RPD. Disappears once billing is enabled on the project | Anyone | No | https://aistudio.google.com | Official |
| Together AI Startup Accelerator | $15K (< $5M raised) / $30K ($5–10M) / $50K (> $10M) + eng hours | Seed to Series B, AI-native, no equity | No | https://www.together.ai/startup-accelerator | Official |
| Fireworks for Startups | Credits (1-yr expiry; aggregators say up to $10K), higher rate limits | Pre-seed to Series B | No | https://fireworks.ai/startups | Official page, amount unverified |
| Novita Startup Program | Up to $10K over 1 yr, but only up to $1K is granted upfront. The next $5K is matched 1:1 against spend and the final $4K at 2:1, split up to $5K Model API and $5K Agent Sandbox. Treat it as a spend rebate, not a grant | Reviewed on stage, team, backing, traction, current spend, and expected usage; new Novita users. Reviewer inspection of the current page reports venture-backed, Series B or earlier, AI-native | No partner ID, but backing is reviewed | https://startups.novita.ai | Official mechanics; eligibility wording partly from review |
| Groq | Free tier: all models, ~30 RPM / 14.4K RPD, no card. No startup program | Anyone | No | https://console.groq.com | Official |
| Mistral | Startup page currently dormant (404). Free plan: $10/mo API credits | Contact sales | n/a | https://mistral.ai/pricing | Unverified/inactive |
| Cohere Startup Program | **Historical / unverified / possibly inactive.** Earlier program text described ~25% off for 12 months for Series B or earlier startups, but as of 2026-09-05 the application URL redirects to Cohere's homepage and no current intake or terms page was found. Excluded from all totals | Historical: Series B or earlier | n/a | https://cohere.com (application URL redirects; accessed 2026-09-05) | Unverified; no current intake found |
| xAI (Grok) API | $25 signup; +$150/mo if you opt into training on your traffic. No program | Anyone | No | https://x.ai/api | Semi-verified |
| NVIDIA Build / NIM API | ~1,000 free inference credits, prototyping only | Anyone | No | https://build.nvidia.com | Official |
| Z.ai (Zhipu) GLM | Free GLM-4.5-Flash; 8M tokens/day trial for 5 days | Anyone | No | https://z.ai/model-api | Official |
| Alibaba Model Studio (DashScope / Qwen) | ~1M free tokens per model, 90 days | New accounts | No | https://www.alibabacloud.com/help/en/model-studio/new-free-quota | Official |
| DeepSeek, Moonshot/Kimi, MiniMax | No startup credit program found on the official platform or pricing pages; only small signup vouchers or trial credits | n/a | n/a | https://platform.deepseek.com, https://platform.moonshot.ai, https://platform.minimax.io (accessed 2026-09-05) | Unverified absence: no program page found, which is not proof that none exists |
| Ollama | Local: free and unlimited. Ollama Cloud free tier is small | Anyone | No | https://ollama.com/pricing | Official |
| Nous Portal | Free tier with free-model catalog; Plus $20/mo → $22 credits | Anyone | No | https://portal.nousresearch.com | Official |
| Perplexity for Startups | $5K API credits + 6 mo Enterprise Pro | < $20M raised, < 5 yrs, via Perplexity Startup Partner | Yes | https://www.perplexity.ai/startups | Official |

### 2b. Cloud, compute, and terminal backends (Docker, Modal, Daytona, Lambda, VPS)

| Program | Worth | Eligibility | Referral needed? | Link | Confidence |
|---|---|---|---|---|---|
| Microsoft for Startups (Azure) | Milestone model: $200 starter credit at Azure sign-up, then up to $5K (milestones 1 and 2) after business verification. Later milestones up to $150K are unlocked automatically by active Azure workloads and sustained usage, not by application. Investor Network-backed startups get expanded credits, up to $150K total per the current Investor Network page, plus Azure support, GPU access, GitHub Enterprise, and Microsoft 365 Business Premium. Some Microsoft benefits pages mention up to $200K for eligible investor-backed startups; the official pages conflict, so $150K is used here | New Azure customer, registered entity. Higher tiers need verified progress and usage; the top tier needs an Investor Network partner | No for $5K; usage-gated above; partner for the top tier | https://www.microsoft.com/en-us/startups and https://learn.microsoft.com/en-us/microsoft-for-startups/benefits/get-more-benefits | Official (2026-09-05) |
| AWS Activate (Bedrock-eligible) | Two direct packages. **Founders**: $1K on approval; selected startups can receive up to $5K over time. **Portfolio**: up to $200K, requires an Activate Provider Organization ID from an accelerator, angel group, or VC. Separately, Stripe Atlas, Mercury, Brex, and YC Startup School each advertise a $5K AWS package for their members; those run through the Provider channel, and AWS does not publish how they interact with each other or with Founders | < 10 yrs, pre-Series B (last round within 12 months), working website, no prior Activate credits of equal or greater value | No for Founders; yes (Org ID) for Portfolio | https://aws.amazon.com/startups/credits/ | Official (2026-09-05); $300K gen-AI tier unverified |
| Cloudflare for Startups | Three tiers, credits valid 1 yr: Tier 3 $10K (no minimum funding), Tier 2 $100K (adds account manager and technical sessions), Tier 1 $350K (adds office hours and priority support). Credits cover usage-based services; core security and networking are free at every tier | Software startup with LinkedIn profile, valid website, and company email. Current three-tier criteria: Tier 3 $10K, bootstrapped or self-funded and under $1M raised (the program page also states no minimum funding is required); Tier 2 $100K, under $5M raised plus an affiliated Cloudflare partner (accelerator or VC); Tier 1 $350K, $5M or more raised plus an affiliated partner. **Payment method required**: you must add a valid card, and once credits are consumed or expire Cloudflare bills that card for continued usage unless you sign a prepaid contract. A tier upgrade does not reset the 12-month expiry | No for Tier 3; Tier 2 and Tier 1 require an affiliated partner | https://www.cloudflare.com/startups/ (program page and FAQ, accessed 2026-09-05) | Official tiers and billing terms; funding thresholds from the program FAQ as reported by the independent review, not reproduced from this environment |
| Daytona Startup Grid | $10K on approval, up to $50K; $25K immediate with partner VC referral | AI/agent startups; pitch deck + 100-word story | No | https://www.daytona.io/startups | Official |
| Modal Startup Program | Up to $25K credits, 12 mo. Starter plan: $30/mo free compute | New to Modal; Seed–Series A via Modal VC partner or > $1M raised | Effectively yes | https://modal.com/startups | Official |
| Lambda GPU cloud | $7,500 credits for NVIDIA Inception members; research grant up to $5K | NVIDIA Inception membership | Via Inception | https://lambda.ai | Official snippet, URL unverified |
| NVIDIA Inception | Free membership: DLI credits, DGX Cloud discounts, partner credits (AWS up to $100K, Nebius up to $150K, Lambda $7.5K), VC intros | Incorporated, < 10 yrs, >= 1 developer, website | No | https://www.nvidia.com/en-us/startups/ | Official |
| Intel Liftoff | Free: Tiber Developer Cloud access (Xeon 6, Gaudi), 1:1 engineering mentorship | Early-stage AI/ML startups | No | https://www.intel.com/content/www/us/en/developer/tools/oneapi/liftoff.htm | Official |
| DigitalOcean Hatch | Core credits up to $100K over 12 mo; the award varies by partner and by startup. Core credits **do not cover GPU Droplets**. GPU credit packages are separate, granted only to selected participants after a GPU application review; Hatch members otherwise get GPU Droplets at a discounted hourly rate | <= $10M raised, up to Series A, business email; AI-native prioritized | Direct or via partner | https://www.digitalocean.com/startups | Official (2026-09-05); age limit to confirm |
| Neon / Databricks Startup Program | Two tiers. **Self-funded tier**: up to $1,000 in Neon credits, counted in the bootstrapped and confirmed totals. **Venture-backed tier**: up to $200K in credits across Databricks and Neon combined, amount depends on stage and funding, no fixed Neon-only allocation, so excluded from the partner-backed totals. Credits valid 12 months from acceptance | Self-funded: under $1M raised, early product development. Venture-backed: at least $1M raised or a recognized accelerator | No for self-funded tier | https://neon.com/startups and https://www.databricks.com/product/startups (accessed 2026-09-05) | Official |
| Render Startup Program | $5K (accelerator) / $10K (< $1M raised) / $25K ($1M+) / $100K Scale AI ($2.5M+) | Pre-seed to Series A | Partly | https://render.com/startups | Third-party; official page blocked |
| Vercel for Startups | Up to $30K credits | <= Series A, within 12 mo of round, **must** be partner-affiliated | Yes | https://vercel.com/startups/credits | Official |
| Vercel Open Source Program | $3,600 credits + partner starter pack, quarterly cohorts | Actively maintained OSS project | No | https://vercel.com/open-source-program | Official |
| OVHcloud Startup Program | Start EUR 10K + 6 hrs engineering; Scale up to EUR 100K | < 5 yrs, < 50 employees, < EUR 10M revenue | No | https://startup.ovhcloud.com/en/ | Consistent third-party |
| Oracle for Startups | $300 free trial + Always Free; larger credits via VC partners (amounts unverified) | Sign up | Partly | https://www.oracle.com/cloud/oracle-for-startups/ | Unverified |
| MongoDB for Startups | Historically up to $5K Atlas credits; tiers now unpublished | < 7 yrs, <= Series A | No | https://www.mongodb.com/solutions/startups | Unverified |
| Supabase | ~$300 credits or ~6 mo Team plan via partner accelerators | Partner affiliation | Yes | https://supabase.com/solutions/startups | Unverified |
| Railway | Historical only. Railway announced a $5K-credit startup program in April 2024; the former program URL is dead and no verified live intake exists as of 2026-09-05. Excluded from all totals | Historical: funded startups | n/a | https://railway.com/changelog/2024-04-26-startup-program (historical changelog, accessed 2026-09-05) | Unverified; no live intake |
| Docker | No credit program. Docker Personal (Desktop, Hub, 1 private repo) free for < 250 employees and < $10M revenue | | No | https://www.docker.com/pricing/ | Official |
| Fly.io, Hetzner | No startup credit program found. Fly.io publishes usage pricing only; Hetzner offers a EUR 50 open-source/API developer credit | n/a | n/a | https://fly.io/pricing, https://developers.hetzner.com/cloud/ (accessed 2026-09-05) | Unverified absence: no program page found, which is not proof that none exists |

### 2c. Web search, scraping, and browser tools (Firecrawl, Tavily, Exa, Parallel, Brave, Browserbase, Browser Use)

| Program | Worth | Eligibility | Link | Confidence |
|---|---|---|---|---|
| Firecrawl | 1,000 credits/mo free, renews monthly, no card. No startup program | Anyone | https://www.firecrawl.dev/pricing | Official |
| Tavily | 1,000 credits/mo free, no card. Startup plan is paid ($220/mo) | Anyone | https://www.tavily.com/pricing | Official |
| Exa | $20 signup + $10/mo free; $1,000 startup/education credits by application | Startups, education | https://exa.ai/pricing | Semi-verified |
| Parallel Web Systems | $5/mo free credits (card required), up to $80 signup; up to $250 startup credits by application | Qualified startups | https://parallel.ai/pricing | Official |
| Brave Search API | Free plan removed Feb 2026. Now $5 free credit/mo per plan (up to $20/mo) with card | Anyone | https://api-dashboard.search.brave.com/app/plans | Official |
| Browser Use Cloud | Free tier + one-time $15 credit | Anyone | https://browser-use.com/pricing | Official |
| Browserbase | Free plan; Startup plan is paid ($99). No credit program found | | https://www.browserbase.com/pricing | Official |

### 2d. Voice, image, and video (ElevenLabs, Fal, Krea, edge-tts)

| Program | Worth | Eligibility | Link | Confidence |
|---|---|---|---|---|
| ElevenLabs Startup Grants | 33M characters (~680 hrs audio) free for 12 mo, ~$4K value | < 25 employees; no VC needed; ~1-week decision | https://elevenlabs.io/startup-grants | Official |
| fal Startup Program | $1K → $5K as usage grows; YC/a16z portfolio $50K serverless or $20K model API; EF $10K. General program is Europe and Asia only | Region or partner limited | https://fal.ai/startups | Official |
| Krea API | Pay as you go; app free tier 100 CU/day. No program | | https://www.krea.ai/app/api | Official |
| edge-tts | Free. Uses an unofficial, reverse-engineered client for the remote Microsoft Edge read-aloud endpoint; not a Microsoft-supported API, no SLA, and access can change without notice. **Do not send sensitive or customer text** through it | Anyone | https://github.com/rany2/edge-tts (accessed 2026-09-05) | Unofficial tool; not a program |

### 2e. Memory layers (Honcho, Supermemory, Mem0, Hindsight)

| Program | Worth | Link | Confidence |
|---|---|---|---|
| Honcho (Plastic Labs) | $100 free credits on signup; $2/M tokens ingested; storage and retrieval free | https://honcho.dev | Official |
| Supermemory | Free: $5/mo usage (~1M tokens + 10K searches), unlimited storage; free production tier for qualifying early-stage startups by application | https://supermemory.ai/pricing | Official |
| Mem0 Hobby | Free: 10K memories, 1K retrieval calls/mo, unlimited end users | https://mem0.ai/pricing | Official |

### 2f. Messaging platforms (Telegram, Discord, Slack, Teams, WhatsApp, SMS)

| Program | Worth | Eligibility | Link | Confidence |
|---|---|---|---|---|
| Telegram Bot API | Free, unlimited bots and messages (~30 msg/s broadcast) | Anyone | https://core.telegram.org/bots/faq | Official |
| Discord API | Free; no cash startup program. Bot verification required past 100 servers | Anyone | https://discord.com/developers | Official |
| Slack | 50% off first 3 mo of monthly Pro (<= 200 employees); 25–30% off 12 mo via Mercury/Brex/accelerator partners | See left | https://slack.com/partner-offers | Partly unverified |
| Microsoft Teams / M365 | Free or discounted M365 Business Premium via Microsoft for Startups | Microsoft for Startups member | https://learn.microsoft.com/en-us/microsoft-for-startups/benefits | Official |
| Twilio (SMS, WhatsApp Cloud) | No evergreen startup credits. AI Startup Searchlight 2026: Track 1 (10 honorees) up to $5K Twilio credits; Track 2 (20 honorees) up to $10K Twilio credits; **deadline Sept 11, 2026**. The landing page also lists up to $2,500 one-time OpenAI API credits per honoree, but Twilio's track summaries and prize FAQ conflict on this component, so treat it as **CONFIRMATION_REQUIRED** with Twilio before counting it | < $200M raised, built on Twilio | https://www.twilio.com/en-us/lp/twilio-ai-startup-searchlight | Official |

### 2g. Dev tooling and workspace (GitHub, Notion, Airtable, observability, support)

| Program | Worth | Eligibility | Referral needed? | Link | Confidence |
|---|---|---|---|---|---|
| GitHub for Startups | $10,000 flexible credits, 12 mo: Enterprise, Copilot (incl. premium models and agents), Advanced Security, Actions | <= Series B, new to Enterprise, no prior credits | Yes (partner) | https://github.com/enterprise/startups | Official |
| GitHub Copilot Free / Actions | Copilot Free: 2,000 completions/mo. Actions: unlimited minutes on public repos; 2,000 min/mo private on Free | Anyone | No | https://github.com/features/copilot/plans | Official |
| Notion for Startups | Business plan + Notion AI free: 6 mo via partner, 3 mo direct | New customer, < 100 employees | No (3 mo) | https://www.notion.com/startups | Official |
| Airtable | No official startup page found; ~$500–$2,000 credits via perk platforms | | | https://airtable.com/pricing | Unverified |
| PostHog for Startups | $50K credits, valid 12 months from application. Policy change with a future effective date: **from September 14, 2026**, credits can no longer be applied to PostHog AI tools (PostHog Desktop, Slack app, Replay Vision, PostHog AI, Inbox). Until that date credits still cover those tools, and usage incurred before the cut-off can still be paid with credits afterward | < 2 yrs old, < $5M raised, company-domain account | No | https://posthog.com/startups and https://posthog.com/handbook/marketing/startups | Official (2026-09-05) |
| Sentry for Startups | Up to $5,000 credits + priority support, 1 yr | Pre-seed to Series A | No | https://sentry.io/for/startups/ | Official |
| Datadog for Startups | Up to $100,000 credits, 1 yr | <= Series A, new to Datadog | Yes | https://www.datadoghq.com/partner/datadog-for-startups/ | Official |
| Segment Startup Program | **Unverified / likely inactive.** As of 2026-09-05 the program URL https://segment.com/startups/ redirects to Twilio's startups page (https://www.twilio.com/en-us/solutions/startups), which states Twilio does not offer additional startup credits. Older Segment docs still describe up to $25K in credits toward the Team plan for up to 2 years, but no current first-party terms page was found, so Segment is excluded from every total | Historical: incorporated < 24 mo, < $5M raised | n/a | https://www.twilio.com/en-us/solutions/startups and https://segment.com/docs/guides/usage-and-billing/discounts-for-startups-npos/ (accessed 2026-09-05) | Unverified; current intake not found |
| Retool for Startups | 100% off Team/Business for 1 yr (up to $60K); yr 2: 25% off | < $10M raised, founded within 10 yrs | No | https://retool.com/startups | Official |
| Linear for Startups | Up to 6 mo free Basic or Business | < 50 employees | Yes | https://linear.app/startups | Official |
| Intercom Early Stage | 93% off yr 1 ($33/mo Advanced), 50% yr 2, 25% yr 3 | < 15 employees, <= $10M raised | No | https://www.intercom.com/early-stage | Official |
| Zendesk for Startups | Suite Professional free: 6 mo baseline, 1–2 yrs with partner | < 250 employees, <= Series B, bootstrapped OK | No (6 mo) | https://www.zendesk.com/startups/ | Official |
| HubSpot for Startups | 90% off yr 1 / 50% yr 2 / 25% ongoing (partner); 30% / 15% via entrepreneurial orgs | < $20M raised, <= Series A | Partly | https://www.hubspot.com/startups | Lightly verified |
| Vanta for Startups | $1,000 discount, new customers | Early stage | No | https://www.vanta.com/solutions/startup | Official |
| Drata Startup Program | Preferred first-contract benefits (no % published) | Investor on Drata's partner list | Yes | https://drata.com/partner/startup-program | Value unverified |
| Atlassian for Startups | Jira, Confluence, Loom, Bitbucket free 12 mo, up to 50 users | <= $10M raised, partner-affiliated | Yes | https://www.atlassian.com/software/startups | Official |
| Zoom for Startups | 1 yr Workplace Business Plus, up to 25 seats | Pre-seed to Series A, partner-affiliated | Yes | https://www.zoom.com/en/lp/zoom-for-startups/ | Official |
| Google Workspace for Startups | Business Plus free 12 mo (up to 200 users), via Google Cloud program | Funded within 5 yrs; no paid Workspace in prior 31 days | Yes (funding) | https://cloud.google.com/startup/benefits | Official |
| Miro Startup Program | $500 credit direct / $1,000 via partner | <= Series A, < 30 employees | No ($500) | https://help.miro.com/hc/en-us/articles/360014912819 | Official |
| 1Password | No formal program; $100 credit via Brex; 6 mo free via some accelerators; free Teams for OSS | | Partly | https://1password.com/pricing/business | Unverified |
| Postman | Free plan is single-user since Mar 2026 | | | https://www.postman.com/pricing | Official |
| Figma for Startups | Up to 100% off Professional + FigJam for 1 yr (third-party only) | < $10M raised, partner-affiliated | Yes | https://www.figma.com/pricing/ (no official startup-program page found; accessed 2026-09-05) | Unverified |

### 2h. Identity, banking, and perk platforms (the unlock keys)

| Platform | Cost | What it unlocks | Link | Confidence |
|---|---|---|---|---|
| YC Startup School | Free, no application | $5K AWS, Stripe, GCP, HubSpot and other deals; co-founder matching | https://www.startupschool.org/faq | Official |
| Stripe Atlas | $500 one-time (Delaware C-corp or LLC + EIN + first year of Delaware registered agent). The registered agent auto-renews at $100 per year after the first year unless cancelled with 30 days notice (https://support.stripe.com/questions/managing-your-registered-agent-subscription) | $2,500 in Stripe product credits, applied automatically to eligible Atlas companies incorporated on or after 2025-10-16, valid for one year after incorporation against eligible Stripe product fees; realized value depends on the eligible fees you actually incur, not on approval or processing volume (https://docs.stripe.com/atlas/signup and https://support.stripe.com/questions/atlas-fee-credits-faq). Stripe also states over $50K in partner discounts, naming Google, Xero, and OpenAI as examples, plus AWS credits surfaced in the Atlas perks tab. The live perk list is only visible after incorporation, each partner sets its own terms and expiry, and offers are discretionary and change; do not treat any specific third-party perk as guaranteed | https://stripe.com/atlas and https://support.stripe.com/questions/stripe-atlas-perks-partners (accessed 2026-09-05) | Official; partner list discretionary |
| Mercury Perks | Free with business account | $5K AWS, $5K Azure, Notion 6 mo + AI, Slack, GitHub, 1Password. Google Cloud perk paused | https://mercury.com/perks | Official |
| Brex Partner Perks | Free with card/banking | $5K AWS, Google Cloud up to $200K over 2 yrs, $1K OpenAI, QuickBooks 30%, Slack | https://www.brex.com/support/brex-partner-perks | Official |
| Carta Launch | Free | Cap table, SAFEs, share issuance (< 25 stakeholders, < $1M raised) | https://carta.com/equity-management/launch/ | Official |
| AngelList | Free | Up to ~$5,600 perks by application (third-party figure) | https://www.angellist.com (no dedicated perks page found; accessed 2026-09-05) | Unverified |
| F6S, FounderPass, NachoNacho | Free basic tiers; paid upgrades | Small SaaS discounts, AWS/DO/Notion listings | https://www.f6s.com https://www.founderpass.com https://nachonacho.com/marketplace | Unverified |
| Secret (joinsecret.com) | $149/yr or $399 lifetime | ~580 deals incl. AWS, GCP, Notion, HubSpot, Airtable, Z.ai $500 | https://www.joinsecret.com/startups | Unverified; reports of deal rejections |
| Product Hunt Founder Club | Was $60/mo | Reportedly discontinued | https://www.producthunt.com (no live Founder Club page found; accessed 2026-09-05) | Unverified |
| GitHub Student Developer Pack | Free (enrolled students only) | GitHub Pro, $100 Azure, 50+ tools | https://education.github.com/pack | Official |

### 2i. Accelerators (only if you want the partner key)

| Program | Terms | Why it matters here |
|---|---|---|
| Techstars | $20K post-money convertible equity agreement for 5% common stock, plus an uncapped MFN SAFE that converts at the next priced round of $1M or more and adds further dilution on top of the 5%. The SAFE is $200K in most regions ($220K total) but $100K for Asia-Pacific programs ($120K total). Both instruments come with a side letter that grants Techstars pro-rata rights in future rounds, information rights (regular reporting of key metrics and burn), drag-along rights, digital-asset provisions, and regulatory and tax covenants, creating an ongoing shareholder relationship with obligations at priced rounds and exits (https://www.techstars.com/investment-terms and https://www.techstars.com/newsroom/investment-terms, accessed 2026-09-05) | Google Cloud lists Techstars among its accelerator partners (Google Cloud accelerator-partnership announcement: https://cloud.google.com/blog/topics/startups/google-cloud-supports-next-generation-startups/, accessed 2026-09-05; high confidence for the partnership itself). Partnership is separate from eligibility: Scale tier still requires Google's current institutional-equity or accelerator criteria, an application, and Google's discretionary approval; participation does not automatically qualify a company. Techstars' status as an AWS Activate Provider, or as a partner for Anthropic, Vercel, or Perplexity, was not verified here |
| 500 Global Flagship | $150K for 6%, 4-month program (https://flagship.aplica.500.co, program application page; low confidence, terms not reproduced from an official terms page here) | Google Cloud lists 500 Global among its accelerator partners (Google Cloud accelerator-partnership announcement: https://cloud.google.com/blog/topics/startups/google-cloud-supports-next-generation-startups/, accessed 2026-09-05; high confidence for the partnership itself). Partnership does not automatically qualify a company for Scale; Google's current eligibility criteria, application, and discretionary approval still apply. AWS, Anthropic, Vercel, and Perplexity partner status not verified here |
| Antler | ~$100–150K US pre-seed; region-specific terms (https://www.antler.co; low confidence, figures from third-party summaries); claims of $650K+ in AI credits are unverified | Google Cloud lists Antler among its accelerator partners (Google Cloud accelerator-partnership announcement: https://cloud.google.com/blog/topics/startups/google-cloud-supports-next-generation-startups/, accessed 2026-09-05; high confidence for the partnership itself). Partnership does not automatically qualify a company for Scale; Google's current eligibility criteria, application, and discretionary approval still apply. AWS, Anthropic, Vercel, and Perplexity partner status not verified here |

### 2j. US government and tax

| Program | Worth | Eligibility | Link |
|---|---|---|---|
| Federal R&D credit payroll offset (IRC 41(h)) | The research credit you actually compute can be applied against employer payroll tax instead of income tax, capped at $500K per tax year. The election can be made for at most 5 tax years, so the theoretical maximum is five elections of up to $500K each; the real figure is whatever Form 6765 yields, typically far less. Do not estimate it from a percentage of spend; have a tax professional compute it | Qualified small business: under $5M gross receipts in the credit year and no gross receipts for any tax year more than 5 years earlier; elect on Form 6765 with a timely filed original return | https://www.irs.gov/instructions/i6765 and https://www.irs.gov/businesses/small-businesses-self-employed/qualified-small-business-payroll-tax-credit-for-increasing-research-activities |
| NSF SBIR/STTR (America's Seed Fund) | Phase I up to $305K; Phase II up to $1.25M | Defensible research thesis; deadlines Nov 4 2026, Mar 4 2027 | https://seedfund.nsf.gov |
| California research credit | Nonrefundable. Unused credit carries over until exhausted and must be applied to the earliest year possible. Credit limited by tax liability cannot be elected refundable. For tax years 2024 through 2026 total business credits cannot reduce tax by more than $5M | California-source qualified research; claim on Form FTB 3523 | https://www.ftb.ca.gov/forms/2025/2025-3523-instructions.html (accessed 2026-09-05) |
| Arizona R&D refundable credit | Partial refund of up to 75% of the credit that exceeds tax liability, capped at $100K per taxpayer per year, from a $5M annual state pool on a first-come basis, with a 1% processing fee. Otherwise the credit is nonrefundable and carries forward. **Not currently actionable**: the Arizona Commerce Authority reports the 2026 calendar-year refund cap is fully allocated, so no new 2026 refund approvals are available; the next window is the first business day of 2027 | Fewer than 150 full-time employees worldwide; apply to the Arizona Commerce Authority and obtain certification before filing | https://www.azcommerce.com/incentives/research-development-tax-credit/rd-refundable-tax-credit/ (accessed 2026-09-05) |
| Connecticut R&D credit exchange | A qualified small business with no tax liability may exchange the credit for a cash refund equal to 65% of its value, capped at $1.5M per income year, via Form CT-1120 XCH filed by the return due date | Gross income for the prior year not over $70M; Connecticut corporation business tax filer | https://portal.ct.gov/drs/publications/corporation-credit-guide/research-and-development-nonincremental-expenses-22mar2022 (accessed 2026-09-05) |
| Other state R&D credits | Most states offer some research credit; refundability, carryover length, and small-business rules differ by state and were not individually verified here. Treat any claim of refundability outside the three states above as unverified | Varies | Unverified |
| Delaware EDGE 2.0 | Grants up to $25K (Entrepreneur) / $100K (STEM), 3:1 match | Requires Delaware operations, not just incorporation | https://www.choosedelaware.com |

## 3. Stacking order

1. **Identity first (week 1).** Incorporate (Stripe Atlas costs $500 plus $100 per year for the registered agent after year one; the $2,500 Stripe credit is automatic for eligible companies incorporated on or after 2025-10-16 but only worth what you spend in eligible Stripe fees within a year, and the $5K AWS package depends on AWS Activate approval, so the $7.5K+ figure is a ceiling, not a guaranteed value). Open Mercury or Brex for banking; each advertises a $5K AWS package, but AWS does not publish how partner packages combine, so expect to use one channel. Join Carta Launch and YC Startup School. Use a domain-matched email everywhere.
2. **Claim the no-referral tiers (weeks 1–2).** Microsoft for Startups ($5K Azure + M365), Cloudflare $10K, Daytona $10K, OpenRouter $5K, Anthropic community tier (community access only, no credits without institutional funding), Novita (only $1K upfront, rest is spend-matched), NVIDIA Inception (then Lambda $7.5K), Intel Liftoff, ElevenLabs grant, PostHog, Sentry, Retool, Intercom, Zendesk, Notion 3 mo, Miro $500, Vanta $1K. Vercel Open Source Program if you keep a genuinely maintained OSS repo. Twilio Searchlight before Sept 11.
3. **Hold Google Cloud Start if a check is coming.** The $2K Start tier counts against the under-$5K prior-credit limit for the $200K–$350K Scale/AI tier.
4. **Understand the partner gates before applying for anything large.** Azure $150K, Google Scale/AI, AWS Portfolio, Anthropic credit tiers (credits available, amount unverified), Datadog $100K, Vercel $30K, GitHub $10K, Perplexity $5K, Linear, Atlassian, Zoom, and Figma each have their own partner or funding rules, and they differ. Google's Scale tier accepts equity investment (including SAFEs) only from institutional investors and VC firms; angel, friends-and-family, crowdfunding, grants, and prize money do not qualify. Vercel, GitHub, and Datadog require affiliation with their own approved partner lists regardless of how much you raised. Do not raise money, sign a SAFE, or take on equity or legal obligations in order to unlock credits; raise only when the business needs capital, then apply within 12 months of the round.
5. **Stagger activations.** Most credits last 12 months. Activate Azure, then GCP, then AWS as your compute grows.
6. **Tax layer.** Once you pay W-2 wages, have a tax professional compute the research credit on Form 6765 and decide whether the 41(h) payroll election is worth making on that year's timely original return. Consider SBIR only with a real research thesis.
7. **Defer paid aggregators** (Secret, FounderPass premium) until SaaS spend exceeds ~$200/mo.

## 4. Deadlines and recent changes to know

- Twilio AI Startup Searchlight closes **Sept 11, 2026**.
- PostHog: **from Sept 14, 2026**, startup credits stop covering PostHog AI tools. Before that date they still apply, and usage incurred before the cut-off remains payable with credits (https://posthog.com/handbook/marketing/startups).
- Brave Search API free plan was removed in Feb 2026; a card is now required for the $5/mo credit.
- Gemini API free tier disappears the moment billing is enabled on the project.
- Microsoft for Startups dropped bundled OpenAI credits in July 2025; use Azure OpenAI from the Azure balance instead.
- Mercury's Google Cloud perk is paused; use Brex or apply to Google directly.
- Mistral's startup program page is down; treat it as inactive.
- Postman Free became single-seat in March 2026.
- DigitalOcean's $200 student credit retired Aug 1, 2026.
- xAI's $150/mo credit requires opting into training on your API traffic. Do not use it with customer data.

## 5. Re-running this research locally with Hermes

The research passes above were run from a cloud environment. To re-run or cross-check with a local
model through Hermes and Ollama:

```bash
hermes -m qwen3:8b --provider ollama -t web -z "Here is my startup: an AI-agent product built on the hermes-agent stack (OpenAI, Anthropic, OpenRouter, Gemini, Groq, DeepSeek, Mistral, Modal, Daytona, Lambda, Docker, Firecrawl, Tavily, Exa, Browserbase, ElevenLabs, Fal, Notion, Airtable, GitHub, Slack, Discord, Telegram). Find every startup credit, free program, and founder discount I qualify for. For each: program, what it is worth, eligibility, how to apply, direct link. Output a markdown table and total the value."
```

Set at least one web-search key (Firecrawl, Tavily, Exa, Parallel, or Brave) so the model verifies
figures instead of recalling them. A small local model will miss programs and mis-state eligibility;
use its output as a second pass against this document.
