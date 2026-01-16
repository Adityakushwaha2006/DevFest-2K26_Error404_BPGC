# 🎯 NEXUS Demo Guide - Search & Scoring

## 🔍 **Discovery Engine Demos**

### **Demo 1: Search for People**
Find developers you don't know yet:

```bash
cd backend
python demo_search.py 1
```

**What it does:**
- Searches for "blockchain engineers" in SF
- Finds Python developers with 100+ followers
- Searches for ML researchers

**Example output:**
```
🔍 Example 1: Find blockchain engineers in San Francisco
Found 10 developers:

1. @vbuterin
   Profile: https://github.com/vbuterin
   Match Score: 145.2

2. @gavinandresen
   Profile: https://github.com/gavinandresen
   Match Score: 132.8
```

---

### **Demo 2: Find Project Contributors**
Discover active contributors to popular projects:

```bash
python demo_search.py 2
```

**What it does:**
- Searches top React repositories
- Gets active contributors
- Can be used to find domain experts

---

### **Demo 3: Full Discovery Pipeline**
Search → Fetch Profiles → Analyze:

```bash
python demo_search.py 3
```

**Combines:**
1. GitHub search
2. Profile fetching
3. Cross-validation

---

## 📊 **Scoring Engine Demos**

### **Demo 1: Momentum Scoring**
See how active someone is RIGHT NOW:

```bash
python demo_scoring.py momentum torvalds
```

**Output:**
```
📊 MOMENTUM ANALYSIS
Momentum Score: 78/100

✅ Status: VERY ACTIVE
   This person is highly engaged right now!

🔥 Activity Bursts:
   1. 2026-01-15: 8 events (high intensity)
   2. 2026-01-12: 5 events (moderate intensity)
```

---

### **Demo 2: Win Probability** ⭐ **THE MAGIC FEATURE**
Should you contact now or wait?

```bash
python demo_scoring.py probability kentcdodds
```

**Output:**
```
🎲 WIN PROBABILITY ANALYSIS

📊 Overall Success Probability: 82.5%

📈 Component Scores:
   • Context Match:    75.0/100
   • Timing/Momentum:  92.0/100
   • Intent Signals:   40.0/100

💡 Recommendation: ✅ ACT NOW - High engagement window
📝 Reasoning: Currently very active; Good profile alignment

⏰ Best Time to Connect: RIGHT NOW
```

---

### **Demo 3: Compare Candidates**
Who should you contact first?

```bash
python demo_scoring.py compare torvalds kentcdodds
```

**Output:**
```
🏆 VERDICT
✅ Contact @kentcdodds first (15.3% higher win probability)
```

---

## 🎯 **Real-World Use Cases**

### **Use Case 1: Find Blockchain Devs to Hire**
```bash
# Step 1: Search
python demo_search.py 1

# Step 2: Check momentum for top candidates
python demo_scoring.py momentum <username>

# Step 3: Compare finalists
python demo_scoring.py compare user1 user2
```

---

### **Use Case 2: Find Collaborators for Project**
```bash
# Find contributors to similar projects
python demo_search.py 2

# Check who's most active
python demo_scoring.py momentum <username>

# Calculate best time to reach out
python demo_scoring.py probability <username>
```

---

## 📈 **Understanding Scores**

### **Momentum Score (0-100):**
- **0-30:** Dormant (hasn't been active recently)
- **30-60:** Moderate activity
- **60-80:** Active (good baseline)
- **80-100:** Very active (high engagement window!)

### **Win Probability (0-100%):**
Formula: `(30% × Context) + (50% × Timing) + (20% × Intent)`

- **0-40%:** Low probability, wait for better time
- **40-60%:** Moderate, consider reaching out
- **60-75%:** Good probability, good time to connect
- **75-100%:** Excellent! Act now!

### **Recommendations:**
- **✅ ACT NOW:** High momentum + good match
- **⚡ GOOD TIME:** Moderate activity
- **⏸️ WAIT:** Low activity period
- **⏳ MONITOR:** Wait for activity spike

---

## 🚀 **Commands Quick Reference**

```bash
# Discovery
python demo_search.py 1  # Search users
python demo_search.py 2  # Find contributors
python demo_search.py 3  # Full pipeline

# Scoring
python demo_scoring.py momentum <username>
python demo_scoring.py probability <username>
python demo_scoring.py compare <user1> <user2>

# Examples
python demo_scoring.py momentum torvalds
python demo_scoring.py probability kentcdodds
python demo_scoring.py compare torvalds kentcdodds
```

---

## 💡 **Your Competitive Advantage**

**What LinkedIn/Happenstance DON'T have:**

1. ✅ **Timing Intelligence** - "When to connect" recommendations
2. ✅ **Win Probability** - Quantified success likelihood
3. ✅ **Activity Bursts** - Detect engagement windows
4. ✅ **Momentum Scoring** - Real-time activity measurement
5. ✅ **Candidate Comparison** - Data-driven prioritization

**Your pitch:**
> "We don't just tell you WHO to connect with. We tell you WHEN to connect and predict your probability of success. Our momentum engine detects activity bursts that indicate the perfect timing window."

---

## 📝 **Next: Integrate Everything**

Now that you have:
- ✅ Identity resolution (GitHub + Dev.to)
- ✅ Discovery engine (search)
- ✅ Scoring engine (momentum + readiness)

**Final step:** Build the UI (Streamlit dashboard) to visualize it all!
