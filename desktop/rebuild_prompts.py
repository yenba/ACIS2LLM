import re

with open("src/App.tsx", "r") as f:
    content = f.read()

old_prompts = """  const suggestedPrompts = [
    "Was this June one of the wettest Junes ever in Lexington KY?",
    "How hot was July 2023 in Denver compared to normal?",
    "Did it snow on Christmas in Chicago last year?",
    "What's the rainiest month on record for Seattle?"
  ];"""

new_prompts = """  const ALL_PROMPTS = [
    "Was this June one of the wettest Junes ever in Lexington KY?",
    "How hot was July 2023 in Lexington KY compared to normal?",
    "Did it snow on Christmas in Lexington last year?",
    "What's the rainiest month on record for Kentucky?",
    "What was the highest temperature recorded in Los Angeles last summer?",
    "How many days did it rain in Camarillo CA last January?",
    "Is Camarillo CA drier than usual this year?",
    "What's the hottest day on record for Fort Myers, FL?",
    "How much rain did Fort Myers get during hurricane season last year?",
    "Has it ever snowed in Waynesville NC?",
    "What was the coldest temperature in Waynesville NC last winter?",
    "What is the average humidity in Memphis TN in August?",
    "How many days over 100 degrees did Memphis TN have last year?",
    "What was the wettest spring on record for Nashville TN?",
    "Did Nashville TN set any temperature records last year?"
  ];

  const suggestedPrompts = useMemo(() => {
    const shuffled = [...ALL_PROMPTS].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, 4);
  }, [currentConversationId]);"""

content = content.replace(old_prompts, new_prompts)

with open("src/App.tsx", "w") as f:
    f.write(content)
