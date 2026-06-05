# Senior/Lead React Interview: The Complete Meta-Game

Landing a senior or lead offer is not about proving you know more — it is about proving you think differently. Interviewers at this level are evaluating judgment, ownership, and the degree to which you multiply those around you. This guide covers every layer of the senior interview loop: behavioral, leadership, architecture narration, live coding, take-homes, negotiation, and the week-before preparation plan.

---

## What "Senior" Actually Means to Interviewers

### The Leveling Rubric Mental Model

Interviewers use an implicit (sometimes explicit) rubric that separates IC levels from lead expectations. Internalizing this rubric changes how you answer every question.

| Dimension | Mid-Level (L4) | Senior (L5) | Staff/Lead (L6) |
|---|---|---|---|
| Scope | Assigned features | Owns a domain | Defines the roadmap |
| Ambiguity | Needs clarity | Creates clarity | Eliminates ambiguity for others |
| Impact | Self | Team | Org or cross-team |
| Mentorship | Receives | Gives informally | Structures programs |
| Trade-offs | Executes chosen path | Identifies options | Sets the decision framework |
| Conflict | Escalates | Resolves | Prevents |

When an interviewer asks "tell me about a hard decision," they are not asking for a technical answer. They are asking: did you identify the axes of the trade-off? Did you involve the right people? Did you own the outcome?

> 💡 Senior insight: If your story has no option B, you haven't told a senior-level story. Every strong answer shows that you considered alternatives and chose deliberately.

### The Multiplier Test

The single question interviewers ask themselves after every answer: "Would this person make the people around them better?" A senior engineer who ships features in isolation is a strong IC. A senior engineer who ships features and leaves the codebase cleaner, the team more capable, and the process more robust — that is the hire.

Frame every behavioral answer through this lens. Your impact is not just what you built; it is what you enabled others to build.

---

## Behavioral Interviews: STAR + L (Lesson)

### The STAR+L Structure

- **Situation**: Set context briefly. Team size, stack, constraints. 2-3 sentences max.
- **Task**: Your specific responsibility. Use "I", not "we" — interviewers need to assess your contribution.
- **Action**: What you did, how you decided, who you involved. This is the bulk of the answer (60%).
- **Result**: Quantified outcome. Lines of code removed, load time reduction, incident MTTR, team velocity delta.
- **Lesson**: What you would do differently. This is what separates seniors — genuine reflection without defensiveness.

Common failure modes: too much Situation, no quantification, "we" throughout, no Lesson.

---

## 12 Senior Behavioral Prompts with Skeletons

### 1. "Tell me about a hard technical decision you made under uncertainty."

**What they're assessing**: Trade-off reasoning, stakeholder communication, comfort with incomplete information.

**Skeleton**:
- S: Migrating a high-traffic React SPA from client-side routing to Next.js during an active product sprint.
- T: I owned the technical decision and migration plan with no dedicated migration window.
- A: Listed the axes: SEO impact (high), team learning curve (medium), deployment complexity (high), performance (positive). Ran a spike on one route in parallel. Socialized a risk-tiered rollout with the PM. Chose a strangler-fig migration pattern — new routes in Next.js, legacy routes untouched until stable.
- R: Shipped first 3 routes in 6 weeks with zero regressions. SEO impressions up 34% in 90 days.
- L: I underestimated shared-state complexity across the boundary. Next time I would define the seam contract before writing a line of migration code.

**Follow-ups they'll ask:**
- How did you get buy-in for the migration?
- What would you have done if the spike failed?
- Who disagreed and why?

---

### 2. "Describe a disagreement with a teammate or manager."

**What they're assessing**: Psychological safety, intellectual honesty, conflict resolution without politics.

**Skeleton**:
- S: My manager wanted to ship a feature with client-side token storage; I believed it was a security risk.
- T: I had to push back without damaging trust or creating a blocker.
- A: I documented the risk with a CVSS score estimate and two CVE references, then proposed an httpOnly cookie alternative with a migration cost estimate. I asked for a 30-minute design review rather than a Slack debate.
- R: We shipped the cookie-based approach. The PM later cited the documented risk review as a model for future security trade-off discussions.
- L: I led with data, not opinion. I also learned to front-load security thinking in the design phase rather than at implementation review.

**Follow-ups they'll ask:**
- What if your manager had still disagreed?
- Have you ever been wrong in a technical disagreement?

---

### 3. "Walk me through a production incident you owned."

**What they're assessing**: Calm under pressure, systematic thinking, blameless culture, prevention mindset.

**Skeleton**:
- S: A React SSR memory leak caused 100% CPU on prod servers during a product launch. P0 at peak traffic.
- T: I was the on-call engineer and incident commander.
- A: Detect — Datadog alert at 02:14. Mitigate — rolled back the previous deploy within 8 minutes. Stabilize — confirmed CPU normalized, notified stakeholders. Root cause — React.renderToString holding references across requests due to a shared mutable object in module scope. Fix — isolated the object to request scope, added heap profiling to CI.
- R: MTTR 22 minutes. Wrote the blameless postmortem with 3 action items, all closed within one sprint.
- L: We had no SSR-specific memory profiling in CI. I now advocate for it as a baseline in any SSR adoption.

**Follow-ups they'll ask:**
- How did you communicate with non-technical stakeholders during the incident?
- What is your error budget philosophy?

---

### 4. "Tell me about a time you mentored a junior engineer."

**What they're assessing**: Investment in others, ability to level up a team, patience, teaching method.

**Skeleton**:
- S: A junior engineer on my team was shipping features but PR review cycles were averaging 4 rounds of feedback.
- T: I wanted to reduce their review friction and increase their technical autonomy.
- A: I did a structured pair session on one of their PRs — not to fix it, but to narrate my review process out loud. I then created a team PR checklist distilling the most common feedback patterns. I also started doing weekly 30-minute design reviews with them before they wrote code.
- R: Their average review rounds dropped from 4 to 1.5 over 8 weeks. They shipped a solo feature with zero regressions in their third month.
- L: I should have done the pair review sooner instead of giving written feedback that lacked context.

**Follow-ups they'll ask:**
- What do you do when a junior engineer is not improving?
- How do you mentor without creating dependency?

---

### 5. "Tell me about a time you missed a deadline or had to cut scope."

**What they're assessing**: Estimation integrity, early escalation, trade-off communication, no blame-shifting.

**Skeleton**:
- S: A redesign of our data visualization layer was scoped for 6 weeks. At week 4 we were 40% complete.
- T: I needed to make a call: slip the date, cut scope, or pull in resources.
- A: I decomposed remaining work, identified which features were launch-blocking vs. nice-to-have, and brought a scope recommendation to the PM with cost/benefit for each cut. I did not wait for the PM to ask — I surfaced the risk with options.
- R: PM accepted a 70% scope ship with a documented follow-on plan. We launched on time. The remaining 30% shipped two sprints later.
- L: My initial estimate was over-optimistic because I did not account for design iteration cycles. I now build 20% buffer for design-heavy work and milestone-check at week 2.

**Follow-ups they'll ask:**
- How do you prevent scope creep in the first place?
- Who was accountable for the initial estimate?

---

### 6. "Tell me about a time you pushed back on a PM or stakeholder."

**What they're assessing**: Ability to hold technical ground, communication skill, relationship preservation.

**Skeleton**:
- S: A PM requested a feature that required storing PII in localStorage for performance.
- T: I needed to say no without derailing the product timeline.
- A: I quantified the actual performance gap the PM was solving for (200ms), then proposed two alternatives that closed 80% of the gap without the security trade-off. I framed it as "here's what I can ship on your date that's safe" rather than "no."
- R: PM accepted alternative 2. Security audit the following quarter flagged zero issues in that area.
- L: PMs respond better to options than to blockers. I now default to "here is what I can do" framing.

---

### 7. "Give me an example of influencing without authority."

**What they're assessing**: Cross-team collaboration, persuasion through data, building credibility.

**Skeleton**:
- S: Our design system had inconsistent button variants across 3 product teams using the same component library.
- T: I had no authority over the other teams' codebases.
- A: I audited all button usages and created a visual diff document. I presented it at the frontend guild with a proposed consolidation. I offered to do the migration work in their repos — removing the cost objection. I also involved the design lead to add design authority to the case.
- R: Consolidated to a single variant system over 2 sprints with all 3 teams. Reduced CSS shipped to users by 18KB.
- L: Volunteering to do the work is the most effective form of influence. Remove friction, don't just argue.

---

### 8. "How have you advocated for paying down tech debt?"

**What they're assessing**: Long-term thinking, business framing, prioritization skill.

**Skeleton**:
- S: Our legacy Redux store had grown to 40 reducers with no normalization, causing frequent cascade bugs.
- T: I wanted to prioritize a refactor in a roadmap full of feature work.
- A: I tracked bugs per sprint attributable to state management over 6 weeks. Translated bug fix time to engineering hours. Presented the cost of inaction (1.2 sprints/quarter) vs. the cost of the refactor (1 sprint). Proposed a "refactor by feature" approach — each new feature touched included state normalization in scope.
- R: Tech debt refactor approved as embedded work. State-related bugs dropped 70% in the following quarter.
- L: Quantifying the cost of inaction is more persuasive than describing the technical problem.

---

### 9. "Tell me about a project that failed."

**What they're assessing**: Self-awareness, intellectual honesty, learning orientation, no blame-shifting.

**Skeleton**:
- S: We attempted to migrate our custom i18n solution to react-intl. The project was abandoned after 3 months.
- T: I was the technical lead.
- A: We underestimated the surface area. Our custom solution had 12 undocumented edge-case behaviors that react-intl did not support out of the box. We tried to bridge them incrementally but the dual-system maintenance cost exceeded the projected savings.
- R: Project cancelled. We documented the edge cases and wrote a custom layer on top of react-intl as a future starting point.
- L: I should have done a 2-day spike documenting every edge case before committing to the migration. I mistakenly assumed the happy path covered 90% of usage. It covered 60%.

**Follow-ups they'll ask:**
- What would you tell a junior engineer who made the same mistake?
- Did you see the failure coming? When?

---

### 10. "Tell me about receiving hard feedback."

**What they're assessing**: Coachability, emotional maturity, growth mindset.

**Skeleton**:
- S: My tech lead told me in a 1:1 that my PRs were too large and "assumed too much context" — making review difficult.
- T: I disagreed initially and had to sit with the feedback.
- A: I reviewed my last 10 PRs with fresh eyes after 24 hours. The feedback was accurate. I started breaking PRs into a setup commit, implementation commit, and test commit. I added PR descriptions with a "what to review first" section.
- R: My review cycle time dropped from 2 days to 4 hours on average. The tech lead cited my PRs as a team example 3 months later.
- L: My first instinct to defend was wrong. A 24-hour rule before responding to structural feedback has served me well since.

---

### 11. "Tell me about leading a major migration or re-architecture."

**What they're assessing**: Planning, stakeholder management, risk management, delivery.

**Skeleton**:
- S: Migrated a class-component-heavy React app (180 components) to hooks over 4 months with no feature freeze.
- T: I designed and led the migration strategy with a team of 4.
- A: Defined a migration order based on dependency depth (leaves first). Created a codemods for trivial cases. Ran dual-mode stories in Storybook for visual regression. Set team norms: no new class components, all new features in hooks. Tracked progress on a public dashboard.
- R: 100% of components migrated. Zero regressions in production. Two junior engineers led their own sub-sections of the migration.
- L: The public dashboard increased team accountability more than I expected. Visibility is underrated as a coordination tool.

---

### 12. "Tell me about a cross-team collaboration challenge."

**What they're assessing**: Communication across boundaries, empathy for other team constraints, shared ownership.

**Skeleton**:
- S: Our frontend team depended on a backend team for a new GraphQL endpoint. Their sprint capacity was committed elsewhere.
- T: I needed the endpoint in 3 weeks without being able to reprioritize their work.
- A: I proposed building a mock server that matched our agreed schema contract. We used MSW to develop against it. Simultaneously, I wrote the integration test suite against the mock so backend could validate their implementation on delivery.
- R: Frontend developed independently for 3 weeks. When the real endpoint landed, integration took 4 hours rather than a week. Backend team adopted the contract-first approach for future cross-team work.
- L: Decoupling via contracts is a force multiplier. Don't let dependencies serialize your work.

---

## Have 6 STAR Stories Ready: The Multi-Question Map

Prepare 6 rich stories from your experience. Each story should be mappable to multiple question types.

**Story Template:**

```
Story title: [project or incident nickname]
Stack/context: [brief]
My role: [IC, lead, on-call, etc.]
Key actions: [3-5 bullet decisions]
Quantified result: [metric]
Lesson: [honest reflection]
Tags: [trade-off | mentorship | failure | conflict | leadership | incident]
```

**Example mapping — one story, many questions:**

| Story | Question it answers |
|---|---|
| Next.js migration | Hard technical decision, influencing without authority, cross-team collaboration |
| Production memory leak | Incident you owned, staying calm under pressure, observability culture |
| Tech debt advocacy | Pushing back on a PM, advocating for quality, business framing |
| Failed i18n migration | Project that failed, receiving feedback, estimation honesty |
| Mentoring junior on PRs | Mentoring story, code review philosophy, team standards |
| GraphQL contract decoupling | Cross-team collaboration, creative problem solving, unblocking the team |

> 💡 Senior insight: When asked "give me another example," you should already have a second story tagged to that dimension. Interviewers test breadth of experience, not the same story retold.

---

## Architecture and Decision Narration

### "It Depends" Done Right

Never say "it depends" and stop. Always complete the sentence with the axes.

**Weak**: "It depends on the use case."

**Strong**: "It depends on three axes: (1) how often the data changes — if it's static, SSG wins; if it's per-request, SSR or client fetching; (2) SEO requirement — if discoverability matters, we need server-rendered HTML; (3) team familiarity with the deployment model — a perfect architecture adopted poorly is worse than a good-enough one executed well."

### Making Assumptions Explicit

At the start of any architecture question, state your assumptions out loud:

- "I'm assuming this is a B2C product with anonymous users, so SEO matters."
- "I'm assuming the team has Kubernetes already, so deployment complexity is not a constraint."
- "I'm assuming we want to optimize for developer velocity first and can revisit performance later."

This signals senior thinking: you know that different assumptions lead to different correct answers.

### Talking Through Trade-offs

Use a consistent frame: capability, cost, risk.

- "Option A gives us [capability]. The cost is [build/ops/learning]. The risk is [what could go wrong]."
- "Option B gives us [capability]. The cost is... The risk is..."
- "Given our constraints, I'd lean toward Option A because [the dominant axis]."

> 💡 Senior insight: Interviewers are not looking for the "right" answer in architecture questions. They are watching how you reason, whether you consider failure modes, and whether you can defend a position while remaining open to new information.

---

## Code Review and Mentorship

### What Good Code Review Looks Like

A senior engineer's PR review has four layers:

1. **Correctness** — Does it do what it claims? Are edge cases handled?
2. **Design** — Is this the right abstraction? Will it survive requirements change?
3. **Readability** — Will the next person understand this without asking you?
4. **Security and performance** — Are there obvious attack surfaces or regressions?

Nitpicks (formatting, naming preferences) are clearly labeled as non-blocking. Blockers are few and well-justified.

**Anti-pattern to avoid**: Reviewing style while ignoring design. The inverse of what matters.

### Upleveling the Team

- Pair reviews: review code together, narrate your thought process — do not just give comments.
- PR templates: codify what "done" means (tests, docs, accessibility checks).
- Architecture decision records (ADRs): normalize writing down why, not just what.
- "Why" feedback: "This will cause a stale closure" is better than "change this."
- Public praise for good patterns in team channels — positive reinforcement scales.

> 💡 Senior insight: The highest-leverage mentorship is not fixing code — it is teaching the mental model so juniors can fix it themselves and teach the next person.

### Balancing Velocity vs. Quality

The false dichotomy: most teams treat velocity and quality as opposing forces. They are not. Low quality creates velocity debt — every future feature carries the weight of the last shortcut.

The conversation to have: "We can ship this in 2 days with no tests, or 3 days with coverage. The 3-day version will take 0.5 days to extend next sprint. The 2-day version will take 2 days. The math favors quality for anything we expect to touch again."

---

## Incident Response and On-Call

### The Calm Framework

```
DETECT   → What is broken? What is the blast radius? Who is affected?
MITIGATE → Stop the bleeding. Rollback, feature flag off, rate limit.
STABILIZE → Confirm mitigation. Monitor for 10 minutes.
COMMUNICATE → Update stakeholders on status and ETA. Plain language.
ROOT CAUSE → Once stable, investigate without time pressure.
POSTMORTEM → Blameless. Timeline, contributing factors, action items.
PREVENT → Action items shipped. Runbooks updated. Monitoring improved.
```

### Error Budgets

An error budget is the acceptable amount of downtime/errors given a reliability target. If your SLO is 99.9% uptime, your error budget is 8.7 hours/year.

In a senior interview, the insight is: error budgets shift the conversation from "did we break it" to "are we spending reliability appropriately to ship fast?" If the budget is healthy, accelerate. If it is burned, slow down and invest in reliability.

### Observability Culture

Three pillars: logs (what happened), metrics (how often/much), traces (where in the system).

A senior engineer asks: "How would we know if this was broken at 3 AM without a user report?" If the answer is "we wouldn't," that is a gap to fix before shipping.

---

## Live Coding Strategy

### Before You Write Code

1. Clarify the problem. Repeat it back in your own words.
2. Ask about constraints: performance? browser support? library restrictions?
3. Define your inputs and outputs with examples.
4. State your approach before coding: "I'm going to start with a brute-force solution and optimize if there is time."

### While You Code

- Narrate: "I'm using a Map here because lookup is O(1) vs O(n) for an array."
- Write readable names. Interviewers grade clarity.
- Write the simplest correct solution first. Optimize second.
- Add a basic test case or two as you go — shows senior thinking.
- Name your edge cases out loud even if you do not have time to code them.

### What NOT to Do

- Go silent for more than 60 seconds.
- Jump to optimization before correctness.
- Use an obscure API without explaining it.
- Apologize for your code — frame uncertainty as thinking, not failure.
- Give up. Say: "I know I'm stuck on X. Let me try a different angle."

> 💡 Senior insight: Interviewers often deliberately make problems ambiguous to see if you seek clarity or make assumptions silently. Asking one good clarifying question is worth more than 10 minutes of coding on the wrong problem.

---

## Take-Home and PR Review Rounds

### Standing Out in a Take-Home

What reviewers look at beyond correctness:

- **Accessibility**: semantic HTML, keyboard navigability, ARIA where needed.
- **Error handling**: what happens when the API fails? When data is empty?
- **Testing**: not 100% coverage, but testing the things that matter — the contract, not the implementation.
- **README**: why you made the decisions you made. The README is the narrative of your judgment.
- **What you skipped and why**: a senior candidate writes "I omitted pagination because the scope said mock data — here is how I would add it."

Avoid: over-engineering to impress. A focused, clean solution beats an elaborate one that is hard to review.

### PR Review Rounds

You are given a PR and asked to review it. Structure your feedback:

1. State your overall read: "This looks like a solid implementation of X. I have two blocking concerns and a few suggestions."
2. Blocking issues first, clearly labeled.
3. Design questions (not blockers): "Have you considered...?"
4. Non-blocking suggestions: "Nit: this could be..."
5. Praise something specific: it signals you actually read the code.

> 💡 Senior insight: In a PR review exercise, reviewing only for bugs is a mid-level response. Seniors also review for design, maintainability, and what is missing (tests, error handling, documentation).

---

## Tech Lead and Leadership Scenarios

### Estimation Under Uncertainty

Use range estimates, not point estimates. "This will take 2-4 weeks depending on API contract stability and design iteration cycles." Explain the variables. Update estimates when variables resolve.

The three-point estimate: optimistic / most likely / pessimistic. Commit to most likely, communicate the range.

### Prioritization

When asked how you prioritize a backlog: use impact × effort as a starting signal, but layer in risk (what breaks if we delay?), dependency (what is blocked by this?), and strategic alignment (what does the company need in the next quarter?).

### Saying No

"No" is a complete sentence, but it is rarely the right one in a leadership context. The senior version: "I can't do X by Friday, but I can do Y by Friday and X by the following Wednesday. Which matters more?"

Offer options. Never just block.

### Managing Scope Creep

Identify it early and name it. "This new requirement is outside the agreed scope. I want to capture it — should we add it to the current sprint, creating a 1-week slip, or log it for the next sprint?"

Making scope change visible removes the ambiguity that lets creep happen.

### Planning a Quarter

A senior engineer's quarterly plan includes: goals (what we ship), constraints (what we cannot do), risks (what might prevent delivery), dependencies (who we need), and a mid-quarter checkpoint date.

> 💡 Senior insight: The mark of a strong tech lead in planning is that they surface the risks before the quarter starts, not after the slip happens.

---

## Questions YOU Should Ask the Interviewer

These questions signal senior thinking and generate information you actually need to make an offer decision.

**Engineering culture:**
- "How does the team handle technical debt? Is there a cadence for it, or does it compete with features?"
- "What does a blameless postmortem look like here? Can you walk me through the last one you did?"
- "How do senior engineers influence the roadmap vs. receiving it from product?"

**Team health:**
- "What is the biggest source of friction the team deals with right now?"
- "What does onboarding look like? How long before a new senior engineer is owning something?"

**Growth:**
- "What do your most successful senior engineers grow into here?"
- "How are technical decisions documented and communicated? Do you use ADRs?"

**Role specifics:**
- "What does the first 90 days look like? What would make it a success from your perspective?"
- "Is this role more individual-contributor senior or leaning toward tech lead responsibilities?"

> 💡 Senior insight: Asking no questions is a red flag. Asking only questions you can Google is a weak signal. Asking about blameless postmortems, tech debt culture, and senior influence on roadmap signals you have been a senior before and you know what matters.

---

## Salary, Leveling, and Offer Evaluation

### Basics

- Know your target number before the first call. Research via levels.fyi, Glassdoor, Blind, and your network.
- Give a range, not a point: "I'm targeting $X–$Y for a senior role, depending on the total comp structure."
- Never anchor low. The first number sets the negotiation floor.
- Negotiate total comp: base, equity (vesting cliff, strike price, liquidity), bonus, signing.

### Leveling

Ask explicitly: "What level would this role be mapped to on your internal ladder?" If they say L5, ask what separates L5 from L6 in their framework. This tells you whether the role has a ceiling.

### Evaluating the Team

Before accepting, have answers to:
- What is the team's attrition rate in the last 12 months?
- Who is my direct manager, and what is their management style?
- What is the on-call burden (pages per week, rotation size)?
- Is the tech stack what they say it is, or what it used to be?

---

## Red Flags in Candidates

Avoid these patterns — interviewers notice all of them.

- **"We" throughout**: "We built X, we decided Y" — I cannot assess your contribution.
- **No quantification**: "It went well" — how well? 10% improvement? 10x improvement?
- **No lesson**: A STAR answer with no reflection signals fixed mindset.
- **Blame in failure stories**: "The PM changed requirements" — own your part.
- **Shallow trade-offs**: "We chose React because it's popular" — no axes, no alternatives considered.
- **Over-engineering answers**: Proposing microservices for a to-do app signals poor judgment.
- **Silence in live coding**: Going quiet signals you are not used to collaborative problem solving.
- **Generic questions to interviewer**: "What does the day-to-day look like?" — weak signal.
- **No curiosity**: Not asking about their codebase, their team problems, their process.
- **Overpromising leadership**: Claiming to have led a team of 10 without being able to describe a conflict resolution.

---

## Green Flags Seniors Show

- Answers assume the audience understands trade-offs, not just outcomes.
- Stories have specific numbers: "18KB bundle reduction," "MTTR of 22 minutes."
- They push back on vague interview questions respectfully: "Can I clarify what you mean by 'hard'?"
- They name alternatives they rejected and explain why.
- They give credit to teammates in stories without hiding their own contribution.
- They ask about blameless postmortems, not just the tech stack.
- They show a progression: "Early in my career I would have... now I..."

---

## Rapid-Fire

Quick-recall across the full senior interview kit.

- What is the STAR+L format? Situation, Task, Action, Result, Lesson.
- What are the three pillars of observability? Logs, metrics, traces.
- What does a blameless postmortem produce? Timeline, contributing factors (no blame), action items, runbook updates.
- What is an error budget? The acceptable amount of unreliability given an SLO target.
- What is the "multiplier test"? Would this person make those around them better?
- Name the four layers of a good code review. Correctness, design, readability, security/performance.
- How do you say "it depends" at the senior level? State the axes: "It depends on X, Y, and Z — given [assumption], I would choose..."
- What do take-home reviewers look for beyond correctness? Accessibility, error handling, testing strategy, README reasoning, what was skipped and why.
- What makes a question to the interviewer signal-rich? It surfaces something you cannot Google and reveals you know what senior work actually looks like.
- What is the first thing you do in a live coding session? Clarify the problem and state your constraints.
- How do you negotiate comp? Know your target range before the call, give a range not a point, negotiate total comp not just base.
- What is scope creep management? Name it, make it visible, present the trade-off explicitly.
- What is a strangler-fig migration? Replacing a system incrementally — new functionality goes into the new system while the old system handles existing paths.
- What is the cost-of-inaction argument for tech debt? Quantify bug-fix hours attributable to the debt vs. the cost of the refactor.
- What is the three-point estimate? Optimistic / most likely / pessimistic — commit to most likely, communicate the range.

---

## Red Flags

- You cannot quantify the impact of anything you have worked on.
- All your stories are about what "we" did — you cannot isolate your own contribution.
- You have no failure story, or your failure story has no lesson.
- You have never pushed back on a product or business decision.
- You cannot name what you would do differently in any project.
- You are unprepared for the question "what do you want to ask me?"
- You treat the technical round as the whole interview — behavioral rounds lose more senior offers than technical rounds.
- You have never mentored anyone and have no plan for how you would.
- Your architecture answers have no failure modes or trade-offs.
- You have not researched the team's public engineering blog, open-source repos, or recent tech decisions.

---

## Final Checklist: One Week Out

**Week before the interview:**

- [ ] Write and practice your 6 STAR stories out loud — time them (90 seconds each).
- [ ] Tag each story to at least 3 behavioral question types.
- [ ] Review the company's engineering blog, public repos, and recent job postings.
- [ ] Know your target comp range and the market data behind it.
- [ ] Re-read files 01-12 of this prep kit — identify any weak areas.
- [ ] Do one live-coding session with a peer or on Pramp/interviewing.io.
- [ ] Draft 5 signal-rich questions for each interview round type (behavioral, technical, hiring manager).
- [ ] Confirm the interview format: panel, sequential, take-home, or loop.

**Day before:**

- [ ] Review your STAR story notes — do not re-read technical docs (trust your depth).
- [ ] Prepare your environment: working mic, stable connection, quiet room.
- [ ] Sleep. Cognitive performance under fatigue degrades trade-off reasoning first.

**Day of:**

- [ ] Have your STAR story cheat sheet off-screen but nearby for blanks.
- [ ] In the first 2 minutes of each round, ask the interviewer what they are looking to learn — calibrate your detail level.
- [ ] After each answer, pause and ask: "Does that level of detail answer what you were looking for?"
- [ ] Close every round by asking a signal-rich question.

> 💡 Senior insight: The senior interview is not a harder version of the mid-level interview. It is a different interview entirely. They are hiring for judgment, ownership, and the ability to operate in ambiguity. Every answer you give should reveal how you think, not just what you know.
