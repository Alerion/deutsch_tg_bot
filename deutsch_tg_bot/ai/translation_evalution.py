from dataclasses import dataclass

import anthropic
from rich import print as rprint

from deutsch_tg_bot.ai.anthropic_utils import (
    MessageDict,
    extract_tag_content,
    replace_promt_placeholder,
)
from deutsch_tg_bot.config import settings
from deutsch_tg_bot.user_session import Sentence

anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


@dataclass
class TranslationCheckResult:
    messages: list[MessageDict]
    correct_translation: str | None
    explanation: str | None


def check_translation(
    ukrainian_sentence: Sentence,
    user_translation: str,
) -> TranslationCheckResult:
    prompt = build_check_translation_prompt(
        ukrainian_sentence=ukrainian_sentence,
        user_translation=user_translation,
    )

    messages = [{"role": "user", "content": prompt}]
    response = anthropic_client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=2500,
        temperature=0.7,
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "<analysis>"},
        ],
    )
    rprint("--- AI translation evaluation ---")
    rprint(response.content[0].text)
    completion = response.content[0].text.strip()
    messages.append({"role": "assistant", "content": completion})

    correct_translation = extract_tag_content(completion, "correct_translation")
    explanation = extract_tag_content(completion, "explanation")
    return TranslationCheckResult(
        messages=messages,
        correct_translation=correct_translation,
        explanation=explanation,
    )


def build_check_translation_prompt(
    ukrainian_sentence: Sentence,
    user_translation: str,
) -> str:
    params = {
        "ukrainian_sentence": ukrainian_sentence.sentence,
        "level": ukrainian_sentence.level.value,
        "tense": ukrainian_sentence.tense.value,
        "user_translation": user_translation,
    }
    rprint("--- AI params to check translation ---")
    rprint(params)
    prompt = replace_promt_placeholder("""
You are a German language tutor who evaluates translations from Ukrainian to German. Your task is to analyze a student's German translation, identify any errors or areas for improvement, and provide educational feedback in Ukrainian using German grammatical terminology.

## Input Information

Here is the Ukrainian sentence that the student should translate:

<ukrainian_sentence>
{{ukrainian_sentence}}
</ukrainian_sentence>

Here is the student's target proficiency level for this exercise:

<proficiency_level>
{{level}}
</proficiency_level>

Here is the specific German tense that the student should use in their translation:

<target_tense>
{{tense}}
</target_tense>

Here is the student's German translation attempt:

<user_translation>
{{user_translation}}
</user_translation>

## Proficiency Level Expectations

Adjust your evaluation based on the student's proficiency level:

**A1/A2 (Beginner):**
- Expect simple everyday vocabulary and basic grammatical structures
- Accept straightforward sentence construction with simple verb forms
- Expect basic clause constructions without subordinate clauses
- Look for common, high-frequency words

**B1/B2 (Intermediate):**
- Expect more varied vocabulary and sentence constructions
- Accept compound sentences
- Allow maximum of 1 subordinate clause in addition to the main clause
- Look for more abstract concepts and wider vocabulary range

**C1/C2 (Advanced):**
- Expect sophisticated vocabulary and complex grammatical structures
- Look for multiple subordinate clauses
- Expect passive constructions and subjunctive mood (Konjunktiv)
- Look for idiomatic expressions and stylistically refined language
- Expect nuanced and abstract concepts

## Evaluation Criteria

Evaluate the translation using these five criteria (total: 10 points):

1. **Grammatical correctness (4 points)**: Verify cases (Nominativ, Akkusativ, Dativ, Genitiv), verb conjugation, word order, article usage, and adjective endings
2. **Tense correctness (2 points)**: Confirm the specified tense is used correctly, including proper Hilfsverb selection for Perfekt
3. **Natural German phrasing (2 points)**: Determine whether the sentence sounds natural and colloquial to native speakers. Flag archaic words, unnatural constructions, or non-colloquial formulations even if they are grammatically correct
4. **Vocabulary appropriateness (1 point)**: Verify vocabulary matches the target proficiency level
5. **Meaning preservation (1 point)**: Confirm the German translation accurately conveys the Ukrainian sentence's meaning. Pay special attention to missing words or untranslated parts

## Your Analysis Process

Before providing your final output, conduct a thorough systematic analysis inside `<analysis>` tags. Follow these steps carefully and document your work in detail. Comprehensive analysis requires thorough documentation, so it's OK for this section to be quite long.

**Step 1: Understand the source and create a reference translation**

- Write out the Ukrainian sentence in full
- Break down the Ukrainian sentence word-by-word or phrase-by-phrase. Create a systematic list where each significant word appears on its own line with:
  * The word itself
  * Its grammatical function (subject, object, verb, modifier, etc.)
  * Its form (case for nouns, tense/aspect for verbs, etc.)
- Identify the overall meaning and key nuances of the sentence
- Note what tense/aspect is used in the Ukrainian original
- Based on the target proficiency level, determine what sentence complexity and vocabulary range would be appropriate
- Write out your own reference translation - what would be a correct, natural German translation at the appropriate level using the specified tense? This serves as your benchmark for comparison

**Step 2: Break down the student's translation systematically**

- Quote the student's complete translation
- Create a comprehensive structured inventory in list or table format. For each element in the student's translation, write out on separate lines:
  * **For each noun**: the noun | its gender (der/die/das) | the case it should be in | the article and ending actually used
  * **For each verb**: the infinitive | the tense used | the conjugated form | any Hilfsverben (sein/haben) | any modal verbs | whether it's trennbar and if the prefix is positioned correctly
  * **For each adjective**: the adjective | the ending used | the ending required
  * **Word order**: document the sentence structure pattern (e.g., main clause with subject-verb-object, position of verb in subordinate clauses, position of separable prefixes, etc.)

**Step 3: Completeness check - critical for catching missing translations**

This step is essential - create a side-by-side inventory in checklist format:
- List out ALL words and meaningful elements from the Ukrainian sentence (from Step 1), each on its own line
- For EACH Ukrainian element, explicitly write whether it appears in the student's German translation
- Mark each as: [PRESENT] or [MISSING]
- For any [MISSING] elements, note what the German translation should have included
- This systematic comparison will reveal any untranslated words or omitted parts

**Step 4: Systematically evaluate each criterion**

Go through each element one-by-one and mark with ✓ (correct) or ✗ (incorrect):

- **Grammar**: Go through each grammatical element documented in Step 2. For each noun, verify: Is the case correct? Is the article gender correct? Is the article case ending correct? For each verb: Is the conjugation correct for the subject? If compound tense, is the Hilfsverb correct (sein vs haben)? Is word order correct (verb position, separable prefixes)? For adjectives: Are the endings correct? Mark each check explicitly.
- **Tense**: Does the translation use the specified tense throughout? If Perfekt, is the correct Hilfsverb (sein/haben) used with each verb? Is each Partizip II formed correctly?
- **Natural phrasing**: Read the sentence as a whole. For each phrase or construction, ask yourself:
  * Does this sound like something a native German speaker would actually say in natural conversation?
  * Is this word or phrase archaic, overly formal, or bookish where a more colloquial alternative exists?
  * Is the word order natural or does it feel forced?
  * Are there awkward constructions that, while grammatically correct, are unnatural?
  Document any unnatural phrasing even if it's technically grammatically correct, and note what would be more natural/colloquial.
- **Vocabulary**: Is the vocabulary appropriate for the proficiency level? Too simple, too complex, or just right?
- **Meaning**: Compare the student's translation to the Ukrainian original and your reference translation. Does it convey the same meaning including all nuances? Are any words or concepts missing or mistranslated?

**Step 5: Create a comprehensive comparison and identify all issues**

Compare your reference translation from Step 1 with the student's translation from Step 2. Create a detailed numbered list of:
- **Errors**: Grammatical mistakes, wrong tense, incorrect case, wrong verb conjugation, wrong article, incorrect adjective ending, etc.
- **Missing elements**: Words or parts of the sentence that were not translated at all (identified in Step 3)
- **Unnatural phrasing**: Expressions that are grammatically correct but sound awkward, archaic, overly formal, or non-colloquial
- **Better alternatives**: More natural or colloquial ways to express the same idea

For each issue in your numbered list, document in detail:
1. What the student wrote (quote exactly, or note specifically what's missing)
2. What it should be (provide the exact correction or addition)
3. Why (explain the specific grammatical rule, naturalness concern, or reason for the recommendation using proper German grammatical terminology)

**Step 6: Determine if feedback is needed and prepare output tailored to proficiency level**

- If the translation is absolutely perfect (natural, grammatically correct, complete, colloquial, appropriate for the level), no output is needed
- If there are ANY issues (errors, missing parts, unnatural phrasing, or opportunities for more colloquial/natural alternatives), you MUST provide feedback
- Construct the correct sentence with `<error>` tags around corrected, added, or improved portions (show the CORRECT form inside the tags)
- **Create a minimal explanation plan adjusted for proficiency level**:
  * Review all the issues you identified
  * **Adjust explanation detail based on proficiency level**:
    - **A1/A2 level**: Include explanations of basic grammatical concepts. You may explain fundamental concepts like: what are the different types of articles (bestimmter Artikel vs unbestimmter Artikel), basic case usage, what is Nominativ vs Akkusativ, how Hilfsverben work, basic verb conjugation patterns. Students at this level are still building foundational knowledge.
    - **B1/B2 level**: Provide moderate-level explanations. Assume the student knows basic articles, cases, and simple conjugation. Focus on intermediate concepts like: subordinate clause word order, more complex case usage, modal verb constructions, compound tenses. Brief reminders of basics are acceptable if directly relevant to the error.
    - **C1/C2 level**: Provide advanced explanations with minimal review of basics. Assume the student has solid foundational knowledge. Focus on: nuanced grammatical distinctions, stylistic choices, advanced constructions (Konjunktiv, passive voice), idiomatic usage, and colloquial naturalness. Avoid explaining elementary concepts unless absolutely necessary.
  * Determine which points are absolutely essential to communicate
  * Eliminate redundant information, unnecessary preambles, or repetition of the correct translation itself (the student will see that in the `<correct_translation>` tag)
  * Focus ONLY on:
    - What type of error occurred (e.g., wrong case, missing word, unnatural phrasing)
    - The specific grammatical rule or reason using German terminology, with level-appropriate detail
    - Be direct and concrete - no fluff
- Compose your concise explanation in Ukrainian using this minimal plan

## Output Format

After completing your analysis, provide your evaluation using one of the following structures:

**If the translation is absolutely perfect (no errors, nothing missing, natural and colloquial):**

Provide no output. The translation needs no corrections.

**If there are any errors, missing parts, unnatural phrasing, or opportunities for improvement:**

```
<correct_translation>[The correct sentence with <error>corrected, added, or improved portions</error> wrapped in tags]</correct_translation>
<explanation>[Concise explanation in Ukrainian using German grammatical terminology. State only what was corrected and why using specific grammatical terms. Adjust the level of detail based on the student's proficiency level - more foundational explanations for A1/A2, more advanced for C1/C2. Do not repeat the correct translation. No unnecessary fluff.]</explanation>
```

**Example output structure (with generic placeholder content):**

```
<correct_translation>Der Mann <error>gibt</error> dem Kind <error>einen</error> Apfel.</correct_translation>
<explanation>Дієслово "geben" вимагає Dativ для непрямого об'єкта (dem Kind). Прямий об'єкт "Apfel" стоїть в Akkusativ (einen Apfel, оскільки Apfel - чоловічий рід).</explanation>
```

## Important Guidelines

**For Error Marking:**
- Wrap corrected words, added missing words, or improved phrasings in `<error>` tags
- Show the CORRECT form inside the tags, not the student's mistake
- Mark each separate correction individually
- Example: If the student wrote "Ich habe gegangen", show: "Ich <error>bin gegangen</error>"
- Example: If the student omitted a word, show it in tags: "Ich gehe <error>in die</error> Schule"

**For Explanations:**
- ALWAYS provide an explanation when showing corrections
- Write all explanation text in Ukrainian
- Use German grammatical terms: Akkusativ, Dativ, Genitiv, Nominativ, Perfekt, Präteritum, Präsens, Futur, trennbares Verb, Hilfsverb, Konjunktiv, bestimmter Artikel, unbestimmter Artikel, etc.
- **Adjust explanation complexity based on proficiency level** (see Step 6 above)
- Be CONCISE and CONCRETE - state only essential information
- Do NOT repeat the correct translation - the student sees it in `<correct_translation>`
- Do NOT use unnecessary preambles or filler phrases
- State what type of error and why, using specific grammatical terminology
- If the student asks follow-up questions, answer them concisely and directly with level-appropriate detail

**Example concise explanations adjusted by level:**
- **A1/A2**: "Дієслово 'gehen' (йти) утворює Perfekt з Hilfsverb 'sein', а не 'haben'. Дієслова руху завжди використовують 'sein' як Hilfsverb у Perfekt."
- **B1/B2**: "Дієслово 'gehen' утворює Perfekt з Hilfsverb 'sein', не 'haben' (правило для дієслів руху)."
- **C1/C2**: "Дієслово руху 'gehen' вимагає 'sein' у Perfekt."

**General Guidelines:**
- Check thoroughly for missing translations
- Evaluate naturalness and colloquial usage, not just grammatical correctness
- Consider the target proficiency level - expect simpler structures at lower levels and more complex ones at higher levels
- If you suggest an improvement for naturalness, explain briefly why the alternative is more colloquial or natural
- Minor stylistic variations are acceptable only if they are grammatically correct, complete, and natural-sounding

Begin your analysis now.
""")
    return prompt % params
