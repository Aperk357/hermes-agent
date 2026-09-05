# Startup Credits, Free Programs, and Founder Discounts for the Hermes Agent Stack

Research date: 2026-09-05. Compiled from four parallel web-research passes over official
provider pages (search-indexed text where direct fetches were blocked) and 2026-dated
third-party guides. Every dollar figure marked **unverified** could not be confirmed against
an official page on the research date. Re-check the linked page before relying on a number.

## 1. Headline numbers

| Path | Cloud + AI credits | SaaS credits / discounts (nominal) | Notes |
|---|---|---|---|
| Bootstrapped, no investor, no accelerator | ~$55K–$60K | ~$160K+ | Azure $5K, GCP $2K, AWS $5K (via Mercury/Brex/Atlas), Cloudflare $5K, Daytona $10K, OpenRouter $5K, Novita $10K, Anthropic $5K (unverified), ElevenLabs ~$4K, Stripe $2.5K, Sentry $5K; plus PostHog ~$50K, Segment $50K, Retool up to $60K |
| One accelerator or institutional pre-seed check | $800K–$1.3M+ | $250K+ | Google AI tier $350K, AWS Portfolio $100K–$200K, Azure $150K, Anthropic up to $100K, Datadog $100K, DigitalOcean $100K, Neon $100K, Cloudflare $250K, Modal $25K, Together $15K–$50K, Vercel $30K, GitHub $10K |
| Payroll tax (once you run W-2 payroll) | Up to $500K/yr for 5 yrs | | Federal R&D credit payroll offset, IRC 41(h), for qualified small businesses |

Most credits expire 6–12 months after activation and are one-time per tier. Stagger activations to
match your compute ramp instead of claiming everything on day one.

## 2. Programs mapped to the tools this repo uses

### 2a. LLM and inference providers (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, and friends)

| Program | Worth | Eligibility | Referral needed? | Link | Confidence |
|---|---|---|---|---|---|
| OpenRouter for Startups | Up to $5,000 credits across 300+ models, 0% platform/BYOK fees for 12 mo; credits expire ~6 mo | Pre-Series B, under ~$500 lifetime spend, company site and email | No | https://openrouter.ai/startups | Official |
| Anthropic Startup Program (Claude for Startups) | API credits, top rate-limit tier, founder sessions. Aggregators: $5K direct, up to $100K via partner VC, $500K for YC batch | Founded < 4 yrs, no prior credits. Community tier open to bootstrapped founders; credit tiers need institutional funding | No for community; yes for larger tiers | https://claude.com/programs/startups | Official page; dollar tiers unverified |
| OpenAI for Startups | Free API credits (~$5K typical, unverified), tier upgrades, engineer time | Must come via partner VC/accelerator, or $1K–$2.5K via Brex/Ramp/Mercury/Microsoft perks | Yes | https://openai.com/startups/ | Official |
| OpenAI Grove | $50K API credits + mentorship, 5-week cohort | Any stage incl. pre-idea; competitive, cohort-based | No | https://openai.com/index/openai-grove/ | Official |
| Google for Startups Cloud Program | Start: $2K. Scale: $200K. AI-first: up to $350K over 2 yrs + up to $10K Anthropic and Fireworks credits. Covers Gemini/Vertex | Start: pre-funded, < 5 yrs, MVP. Scale/AI: institutional pre-seed to Series A or partner accelerator; under $5K prior GCP credits | No for Start; yes for Scale/AI | https://cloud.google.com/startup/apply | Official |
| Gemini API free tier (AI Studio) | Free Flash models, ~10–15 RPM, 250–1,500 RPD. Disappears once billing is enabled on the project | Anyone | No | https://aistudio.google.com | Official |
| Together AI Startup Accelerator | $15K (< $5M raised) / $30K ($5–10M) / $50K (> $10M) + eng hours | Seed to Series B, AI-native, no equity | No | https://www.together.ai/startup-accelerator | Official |
| Fireworks for Startups | Credits (1-yr expiry; aggregators say up to $10K), higher rate limits | Pre-seed to Series B | No | https://fireworks.ai/startups | Official page, amount unverified |
| Novita Startup Program | Up to $10K: $1K upfront, rest matched against spend; 1 yr | Early-stage AI startups | No | https://startups.novita.ai | Official |
| Groq | Free tier: all models, ~30 RPM / 14.4K RPD, no card. No startup program | Anyone | No | https://console.groq.com | Official |
| Mistral | Startup page currently dormant (404). Free plan: $10/mo API credits | Contact sales | n/a | https://mistral.ai/pricing | Unverified/inactive |
| Cohere Startup Program | ~25% discount for 12 mo (discount, not credits) | Series B or earlier | No | https://cohere.com/startup-program-application | Official |
| xAI (Grok) API | $25 signup; +$150/mo if you opt into training on your traffic. No program | Anyone | No | https://x.ai/api | Semi-verified |
| NVIDIA Build / NIM API | ~1,000 free inference credits, prototyping only | Anyone | No | https://build.nvidia.com | Official |
| Z.ai (Zhipu) GLM | Free GLM-4.5-Flash; 8M tokens/day trial for 5 days | Anyone | No | https://z.ai/model-api | Official |
| Alibaba Model Studio (DashScope / Qwen) | ~1M free tokens per model, 90 days | New accounts | No | https://www.alibabacloud.com/help/en/model-studio/new-free-quota | Official |
| DeepSeek, Moonshot/Kimi, MiniMax | No startup programs. Small signup vouchers only | | | | Official |
| Ollama | Local: free and unlimited. Ollama Cloud free tier is small | Anyone | No | https://ollama.com/pricing | Official |
| Nous Portal | Free tier with free-model catalog; Plus $20/mo → $22 credits | Anyone | No | https://portal.nousresearch.com | Official |
| Perplexity for Startups | $5K API credits + 6 mo Enterprise Pro | < $20M raised, < 5 yrs, via Perplexity Startup Partner | Yes | https://www.perplexity.ai/startups | Official |

### 2b. Cloud, compute, and terminal backends (Docker, Modal, Daytona, Lambda, VPS)

| Program | Worth | Eligibility | Referral needed? | Link | Confidence |
|---|---|---|---|---|---|
| Microsoft for Startups (Azure) | $1K instant → $5K after verification. Investor Offer: $100K start, up to $150K–$200K over time. Includes Azure OpenAI, GitHub Enterprise, Microsoft 365 (Teams) | New Azure customer, registered entity. Investor Offer needs Investor Network referral code | No for $5K; yes above | https://www.microsoft.com/en-us/startups | Official |
| AWS Activate (Bedrock-eligible) | Founders: $1K self-serve, $5K via Mercury/Brex/Stripe Atlas/YC Startup School ($5K lifetime cap across third-party channels). Portfolio: up to $100K (page title says $200K) | < 10 yrs, pre-Series B, website. Portfolio needs Activate Provider org ID | No for Founders; yes for Portfolio | https://aws.amazon.com/startups/credits/ | Official; $200K/$300K gen-AI tiers unverified |
| Cloudflare for Startups | $5K (bootstrapped, code BOOTSTRAPPED) / $25K / $100K / $250K Workers credits, 1 yr | Software startup, < 5 yrs, real domain | No for $5K | https://www.cloudflare.com/startups/ | Official |
| Daytona Startup Grid | $10K on approval, up to $50K; $25K immediate with partner VC referral | AI/agent startups; pitch deck + 100-word story | No | https://www.daytona.io/startups | Official |
| Modal Startup Program | Up to $25K credits, 12 mo. Starter plan: $30/mo free compute | New to Modal; Seed–Series A via Modal VC partner or > $1M raised | Effectively yes | https://modal.com/startups | Official |
| Lambda GPU cloud | $7,500 credits for NVIDIA Inception members; research grant up to $5K | NVIDIA Inception membership | Via Inception | https://lambda.ai | Official snippet, URL unverified |
| NVIDIA Inception | Free membership: DLI credits, DGX Cloud discounts, partner credits (AWS up to $100K, Nebius up to $150K, Lambda $7.5K), VC intros | Incorporated, < 10 yrs, >= 1 developer, website | No | https://www.nvidia.com/en-us/startups/ | Official |
| Intel Liftoff | Free: Tiber Developer Cloud access (Xeon 6, Gaudi), 1:1 engineering mentorship | Early-stage AI/ML startups | No | https://www.intel.com/content/www/us/en/developer/tools/oneapi/liftoff.htm | Official |
| DigitalOcean Hatch | Up to $100K over 12 mo ($10K/mo cap), up to 3 mo free GPU Droplets | <= $10M raised, up to Series A, business email; AI-native prioritized | Direct or via partner | https://www.digitalocean.com/startups | Official; age limit to confirm |
| Neon / Databricks Startup Program | Up to $100K Neon credits over 12 mo; Databricks up to $200K combined | VC-backed >= $1M or accelerator; self-funded track for < $1M raised | No for self-funded track | https://neon.com/startups | Official |
| Render Startup Program | $5K (accelerator) / $10K (< $1M raised) / $25K ($1M+) / $100K Scale AI ($2.5M+) | Pre-seed to Series A | Partly | https://render.com/startups | Third-party; official page blocked |
| Vercel for Startups | Up to $30K credits | <= Series A, within 12 mo of round, **must** be partner-affiliated | Yes | https://vercel.com/startups/credits | Official |
| Vercel Open Source Program | $3,600 credits + partner starter pack, quarterly cohorts | Actively maintained OSS project | No | https://vercel.com/open-source-program | Official |
| OVHcloud Startup Program | Start EUR 10K + 6 hrs engineering; Scale up to EUR 100K | < 5 yrs, < 50 employees, < EUR 10M revenue | No | https://startup.ovhcloud.com/en/ | Consistent third-party |
| Oracle for Startups | $300 free trial + Always Free; larger credits via VC partners (amounts unverified) | Sign up | Partly | https://www.oracle.com/cloud/oracle-for-startups/ | Unverified |
| MongoDB for Startups | Historically up to $5K Atlas credits; tiers now unpublished | < 7 yrs, <= Series A | No | https://www.mongodb.com/solutions/startups | Unverified |
| Supabase | ~$300 credits or ~6 mo Team plan via partner accelerators | Partner affiliation | Yes | https://supabase.com/solutions/startups | Unverified |
| Railway | $5K credits for funded startups (2024 launch; current intake unclear) | Funded | Unclear | https://railway.com/startups | Unverified |
| Docker | No credit program. Docker Personal (Desktop, Hub, 1 private repo) free for < 250 employees and < $10M revenue | | No | https://www.docker.com/pricing/ | Official |
| Fly.io, Hetzner | No startup programs (Hetzner: EUR 50 OSS/API dev credit) | | | | Official |

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
| edge-tts | Free (Microsoft Edge TTS endpoint) | | | n/a |

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
| Twilio (SMS, WhatsApp Cloud) | No evergreen startup credits. AI Startup Searchlight 2026: $5K–$10K Twilio + $2,500 OpenAI credits for 30 winners, **deadline Sept 11, 2026** | < $200M raised, built on Twilio | https://www.twilio.com/en-us/lp/twilio-ai-startup-searchlight | Official |

### 2g. Dev tooling and workspace (GitHub, Notion, Airtable, observability, support)

| Program | Worth | Eligibility | Referral needed? | Link | Confidence |
|---|---|---|---|---|---|
| GitHub for Startups | $10,000 flexible credits, 12 mo: Enterprise, Copilot (incl. premium models and agents), Advanced Security, Actions | <= Series B, new to Enterprise, no prior credits | Yes (partner) | https://github.com/enterprise/startups | Official |
| GitHub Copilot Free / Actions | Copilot Free: 2,000 completions/mo. Actions: unlimited minutes on public repos; 2,000 min/mo private on Free | Anyone | No | https://github.com/features/copilot/plans | Official |
| Notion for Startups | Business plan + Notion AI free: 6 mo via partner, 3 mo direct | New customer, < 100 employees | No (3 mo) | https://www.notion.com/startups | Official |
| Airtable | No official startup page found; ~$500–$2,000 credits via perk platforms | | | https://airtable.com/pricing | Unverified |
| PostHog for Startups | ~$50K credits, 1 yr. From Sept 14, 2026 credits exclude PostHog AI products | < 2 yrs old, < $5M raised | No | https://posthog.com/startups | Official |
| Sentry for Startups | Up to $5,000 credits + priority support, 1 yr | Pre-seed to Series A | No | https://sentry.io/for/startups/ | Official |
| Datadog for Startups | Up to $100,000 credits, 1 yr | <= Series A, new to Datadog | Yes | https://www.datadoghq.com/partner/datadog-for-startups/ | Official |
| Segment Startup Program | Up to $50K credits over 2 yrs | Incorporated < 24 mo, < $5M raised | No | https://segment.com/industry/startups | Official |
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
| Figma for Startups | Up to 100% off Professional + FigJam for 1 yr (third-party only) | < $10M raised, partner-affiliated | Yes | (no official page found) | Unverified |

### 2h. Identity, banking, and perk platforms (the unlock keys)

| Platform | Cost | What it unlocks | Link | Confidence |
|---|---|---|---|---|
| YC Startup School | Free, no application | $5K AWS, Stripe, GCP, HubSpot and other deals; co-founder matching | https://www.startupschool.org/faq | Official |
| Stripe Atlas | $500 one-time (Delaware C-corp or LLC + EIN) | $2,500 Stripe fee credits, $5K AWS, ~$50K partner perks (GCP, GitHub, Notion, OpenAI) | https://stripe.com/atlas | Official |
| Mercury Perks | Free with business account | $5K AWS, $5K Azure, Notion 6 mo + AI, Slack, GitHub, 1Password. Google Cloud perk paused | https://mercury.com/perks | Official |
| Brex Partner Perks | Free with card/banking | $5K AWS, Google Cloud up to $200K over 2 yrs, $1K OpenAI, QuickBooks 30%, Slack | https://www.brex.com/support/brex-partner-perks | Official |
| Carta Launch | Free | Cap table, SAFEs, share issuance (< 25 stakeholders, < $1M raised) | https://carta.com/equity-management/launch/ | Official |
| AngelList | Free | Up to ~$5,600 perks by application | | Unverified |
| F6S, FounderPass, NachoNacho | Free basic tiers; paid upgrades | Small SaaS discounts, AWS/DO/Notion listings | https://www.f6s.com https://www.founderpass.com https://nachonacho.com/marketplace | Unverified |
| Secret (joinsecret.com) | $149/yr or $399 lifetime | ~580 deals incl. AWS, GCP, Notion, HubSpot, Airtable, Z.ai $500 | https://www.joinsecret.com/startups | Unverified; reports of deal rejections |
| Product Hunt Founder Club | Was $60/mo | Reportedly discontinued | | Unverified |
| GitHub Student Developer Pack | Free (enrolled students only) | GitHub Pro, $100 Azure, 50+ tools | https://education.github.com/pack | Official |

### 2i. Accelerators (only if you want the partner key)

| Program | Terms | Why it matters here |
|---|---|---|
| Techstars | $220K for 5% common ($200K MFN SAFE + $20K) | Partner for Google Cloud, AWS, Anthropic, Vercel, Perplexity top tiers |
| 500 Global Flagship | $150K for 6%, 4 months | Same partner status |
| Antler | ~$100–150K US pre-seed; claims $650K+ AI credits (unverified) | Same partner status |

### 2j. US government and tax

| Program | Worth | Eligibility | Link |
|---|---|---|---|
| Federal R&D credit payroll offset (IRC 41(h)) | Up to $500K/yr against employer FICA for 5 yrs ($2.5M lifetime); ~6–10% of qualified R&D spend | < $5M gross receipts, no receipts more than 5 yrs back; elect on Form 6765 Section D on a timely original return | https://www.irs.gov/forms-pubs/about-form-6765 |
| NSF SBIR/STTR (America's Seed Fund) | Phase I up to $305K; Phase II up to $1.25M | Defensible research thesis; deadlines Nov 4 2026, Mar 4 2027 | https://seedfund.nsf.gov |
| State R&D credits | 30+ states; refundable for small businesses in CA, AZ, CT, MN, MD, NY | Varies | |
| Delaware EDGE 2.0 | Grants up to $25K (Entrepreneur) / $100K (STEM), 3:1 match | Requires Delaware operations, not just incorporation | https://www.choosedelaware.com |

## 3. Stacking order

1. **Identity first (week 1).** Incorporate (Stripe Atlas if you want $500 to turn into $7.5K+ of Stripe and AWS credits). Open Mercury or Brex and pick one as your AWS $5K channel, since the $5K third-party cap does not stack. Join Carta Launch and YC Startup School. Use a domain-matched email everywhere.
2. **Claim the no-referral tiers (weeks 1–2).** Microsoft for Startups ($5K Azure + M365), Cloudflare $5K, Daytona $10K, OpenRouter $5K, Novita $10K, Anthropic direct tier, NVIDIA Inception (then Lambda $7.5K), Intel Liftoff, ElevenLabs grant, PostHog, Segment, Sentry, Retool, Intercom, Zendesk, Notion 3 mo, Miro $500, Vanta $1K. Vercel Open Source Program if you keep a genuinely maintained OSS repo. Twilio Searchlight before Sept 11.
3. **Hold Google Cloud Start if a check is coming.** The $2K Start tier counts against the under-$5K prior-credit limit for the $200K–$350K Scale/AI tier.
4. **Get a partner affiliation before applying for anything large.** Azure $150K, Google $350K, AWS Portfolio, Anthropic $100K, Datadog $100K, Vercel $30K, GitHub $10K, Perplexity $5K, Linear, Atlassian, Zoom, and Figma all gate on a VC, accelerator, or Startup Partner ID. Cheapest routes: a small angel or VC SAFE, one accelerator, or Brex's Google Cloud referral. Apply within 12 months of the round.
5. **Stagger activations.** Most credits last 12 months. Activate Azure, then GCP, then AWS as your compute grows.
6. **Tax layer.** Elect the 41(h) payroll offset on your first return once you pay W-2 wages. Consider SBIR only with a real research thesis.
7. **Defer paid aggregators** (Secret, FounderPass premium) until SaaS spend exceeds ~$200/mo.

## 4. Deadlines and recent changes to know

- Twilio AI Startup Searchlight closes **Sept 11, 2026**.
- PostHog credits stop covering PostHog AI products from **Sept 14, 2026**.
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
