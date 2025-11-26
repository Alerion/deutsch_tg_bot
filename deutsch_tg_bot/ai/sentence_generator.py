import random

import anthropic

from deutsch_tg_bot.config import settings
from deutsch_tg_bot.deutsh_enums import DEUTCH_LEVEL_TENSES, DeutschLevel, DeutschTense
from deutsch_tg_bot.user_session import Sentence

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def generate_sentence(
    level: DeutschLevel, previous_sentences: list[Sentence], optional_constraint: str | None
) -> Sentence:
    tense = get_random_tense_for_level(level)
    prompt = build_prompt(
        level=level,
        tense=tense,
        previous_sentences=previous_sentences,
        optional_constraint=optional_constraint,
    )
    response = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=1000,
        temperature=1.0,
        messages=[{"role": "user", "content": prompt}],
    )
    completion = response.content[0].text.strip()
    # Parse <ukrainian_sentence> to extract the sentence
    start_tag = "<ukrainian_sentence>"
    end_tag = "</ukrainian_sentence>"
    start_index = completion.find(start_tag) + len(start_tag)
    end_index = completion.find(end_tag)
    ukrainian_sentence = completion[start_index:end_index].strip()
    return Sentence(sentence=ukrainian_sentence, tense=tense)


def get_random_tense_for_level(level: DeutschLevel) -> DeutschTense:
    tenses = DEUTCH_LEVEL_TENSES[level]
    return random.choice(tenses)


def build_prompt(
    level: DeutschLevel,
    tense: DeutschTense,
    previous_sentences: list[Sentence],
    optional_constraint: str | None,
) -> str:
    previous_sentences = [s.sentence for s in previous_sentences]
    prompt = f"""
You are generating Ukrainian sentences for a Telegram bot that teaches German to Ukrainian speakers.
Your task is to create exactly ONE Ukrainian sentence that users will translate into German.

Here is the German proficiency level for this sentence:

<level>
{level.value}
</level>

Here is the target German tense that the translation should naturally use:

<tense>
{tense.value}
</tense>

Here is an optional constraint (this may be empty, or it may contain a specific German word, phrase,
or grammatical structure that should naturally appear in the German translation):

<optional_constraint>
{optional_constraint or ""}
</optional_constraint>

Here are the sentences you have previously generated.
Your new sentence must be completely different from all of these in terms of topic,
vocabulary, grammatical structure, and sentence type:

<previous_sentences>
{"\n".join(previous_sentences)}
</previous_sentences>

# Your Task

Generate a Ukrainian sentence that meets all the requirements below.
Before providing your final sentence, wrap your systematic planning inside
<sentence_planning> tags to ensure all requirements are met.

## Requirements

### 1. Diversity Requirement

Your new sentence must differ from ALL previous sentences in:
- **Topic/subject matter**: Choose from diverse domains such as daily life, work,
  hobbies, travel, family, food, weather, education, health, technology, culture,
  politics, environment, sports, entertainment, etc.
- **Vocabulary**: Use different words than those in previous sentences
- **Grammatical structures**: Use different sentence patterns and constructions
- **Sentence type**: Vary between statements, questions, and commands

### 2. Proficiency Level Requirement

Adjust the complexity of your sentence based on the specified German proficiency level:

**A1/A2 (Beginner):**
- Use simple everyday situations and basic actions
- Use common, basic vocabulary
- Keep sentence structures straightforward with simple verb forms
- Use basic clause constructions

**B1/B2 (Intermediate):**
- Include more complex situations and abstract concepts
- Use varied sentence constructions and a wider vocabulary range
- Use compound sentences and subordinate clauses

**C1/C2 (Advanced):**
- Use sophisticated vocabulary and complex grammatical structures
- Include abstract and nuanced concepts
- Use idiomatic expressions and advanced discourse elements
- Include multiple subordinate clauses, passive constructions, subjunctive mood, and stylistically refined language

### 3. German Tense Requirement

Construct your Ukrainian sentence so that the most natural German translation uses the specified tense:

- **Präsens**: Current states, habits, general facts, or ongoing actions
- **Präsens Futur**: Future meanings expressed using present tense (scheduled events, immediate future)
- **Perfekt**: Completed actions with present relevance or recent past events
- **Präteritum**: Past events, narratives, or formal descriptions of past situations
- **Futur I**: Future plans, predictions, or intentions using "werden + infinitive"
- **Futur II**: Future perfect tense using "werden + past participle + haben/sein"
- **Plusquamperfekt**: Past perfect tense expressing actions completed before another past action

### 4. Optional Constraint Requirement

If the `<optional_constraint>` contains a value, construct your Ukrainian sentence so that when translated into German,
the translation will naturally incorporate the specified German word, phrase, or grammatical structure.

## Planning Process

In your `<sentence_planning>` section, work through each of these steps systematically:

**Step 1: Analyze Previous Sentences**
- List or quote each previous sentence
- Identify what topics have been covered (list specific examples)
- Identify what vocabulary has been used (list specific words)
- Identify what grammatical structures have appeared (note specific patterns)
- Identify what sentence types have been used (statements, questions, commands)
- It's OK for this section to be quite long.

**Step 2: Plan for Proficiency Level**
Based on the specified level, determine what vocabulary complexity and grammatical structures are appropriate. Be specific about what you will use.

**Step 3: Map Tense Requirements**
For the specified German tense, determine exactly what Ukrainian verb forms you will use. Explain how these Ukrainian forms will naturally map to the target German tense when translated.

**Step 4: Plan Optional Constraint Integration** (if provided)
If a constraint is provided, explain exactly how it will appear in the German translation. Then work backwards to plan how you will construct the Ukrainian sentence to achieve this naturally.

**Step 5: Select Novel Topic**
Choose a specific topic that provides good variety from the previous sentences. Be creative and consider diverse domains.

**Step 6: Decide Sentence Structure**
Decide what sentence type (statement, question, or command) and what specific structure will accomplish all your goals while differing from previous sentences.

**Step 7: Draft and Verify**
- Draft your Ukrainian sentence
- Write out the complete German translation in full
- Identify each main verb in the German translation and explicitly label its tense
- Verify the German translation uses the correct target tense
- Verify the proficiency level is appropriate
- Verify the optional constraint is naturally incorporated (if applicable)
- Verify the topic, vocabulary, and structure differ from previous sentences

## Output Format

Your complete response should follow this structure:

```
<sentence_planning>
[Your detailed internal analysis addressing all 7 steps above. This section can be quite long.]
</sentence_planning>

<ukrainian_sentence>
[Your final Ukrainian sentence - nothing else]
</ukrainian_sentence>
```

**CRITICAL**: After completing your planning in the `<sentence_planning>` tags, output ONLY your final Ukrainian sentence inside `<ukrainian_sentence>` tags. Do not include any explanations, translations, notes, or additional text of any kind outside these tags.

Example output structure:

<sentence_planning>
Step 1: Analyze Previous Sentences
[Your analysis here...]

Step 2: Plan for Proficiency Level
[Your planning here...]

Step 3: Map Tense Requirements
[Your planning here...]

Step 4: Plan Optional Constraint Integration
[Your planning here if applicable...]

Step 5: Select Novel Topic
[Your planning here...]

Step 6: Decide Sentence Structure
[Your planning here...]

Step 7: Draft and Verify
[Your draft and verification here...]
</sentence_planning>

<ukrainian_sentence>
[Only the Ukrainian sentence appears here]
</ukrainian_sentence>
"""
    return prompt
