# RTI-Lens Test Inputs

Example inputs for testing the RTI-Lens system features.

---

## 1. RAG Q&A System

### Section-Specific Questions

**Question:** What are common reasons for denial under Section 8(1)(a)?

**Question:** When can Section 8(1)(d) be invoked by ministries?

**Question:** How is Section 8(1)(j) typically interpreted by CIC?

**Question:** What is the difference between Section 8(1)(a) and 8(1)(g)?

**Question:** Can Section 8(1)(h) be used to deny information about completed investigations?

### Denial Pattern Questions

**Question:** Which ministries have highest denial rates?

**Question:** What are the most misused exemption clauses?

**Question:** Common reasons PIOs cite for refusing information?

**Question:** How often are denials under Section 8(1)(d) overturned?

### Appeal Strategy Questions

**Question:** What arguments work best for overturning Section 8(1)(a) denials?

**Question:** How to challenge "third party information" exemptions?

**Question:** Successful precedents for delayed responses?

**Question:** What evidence is needed to prove public interest outweighs exemption?

### Ministry-Specific Questions

**Question:** How does Ministry of Home Affairs handle RTI requests?

**Question:** What's the success rate for appeals against Ministry of Defence?

**Question:** Which ministry is most transparent with RTI responses?

### Procedural Questions

**Question:** What happens when PIO doesn't respond within 30 days?

**Question:** Can CIC impose penalties on PIOs? When?

**Question:** How to prove information is in public interest?

**Question:** What is the time limit for filing first appeal?

### Precedent Search

**Question:** Cases where CIC ordered disclosure despite security concerns

**Question:** Rulings on RTI requests about government contracts

**Question:** Precedents for RTI on judicial appointments

**Question:** Cases where commercial confidence exemption was rejected

---

## 2. Draft Generator

**Available Ministries in Database:**
- Income Tax Department
- Ministry of Corporate Affairs
- Ministry of Defence
- Ministry of Education
- Ministry of External Affairs
- Ministry of Finance
- Ministry of Home Affairs
- Ministry of Personnel, Public Grievances and Pensions
- Ministry of Railways

### Example 1: Security Exemption Challenge
- **Ministry:** Ministry of Home Affairs
- **Section:** 8(1)(a)
- **Context:** I want information about police complaints filed against me in 2023. The PIO denied saying it affects national security. I need this for a court case.

### Example 2: Third Party Information
- **Ministry:** Ministry of Finance
- **Section:** 8(1)(j)
- **Context:** Please provide details of tax notices sent to my company. PIO refused saying it's third party information but I am the company director.

### Example 3: Commercial Confidence
- **Ministry:** Ministry of Railways
- **Section:** 8(1)(d)
- **Context:** I requested tender documents for railway station construction project. They said it's commercially sensitive information. But tender is already awarded.

### Example 4: Cabinet Papers
- **Ministry:** Ministry of Finance
- **Section:** 8(1)(i)
- **Context:** I want minutes of meetings where budget allocation was discussed for infrastructure project. PIO denied under cabinet papers exemption.

### Example 5: Delayed Response
- **Ministry:** Ministry of Personnel, Public Grievances and Pensions
- **Section:** NULL
- **Context:** I filed RTI 90 days ago asking for pension scheme beneficiary list. No response from PIO. I want to know the status and get the information.

### Example 6: Vague Denial
- **Ministry:** Ministry of Defence
- **Section:** 8(1)(a)
- **Context:** I want list of defense contracts awarded in my state last year. They rejected saying security reasons but I only want contract amounts and company names, not technical details.

### Example 7: Personal Information
- **Ministry:** Ministry of Education
- **Section:** 8(1)(j)
- **Context:** I requested my own exam evaluation sheets from university. PIO denied saying it's personal information of third party (examiner). But I have right to my own records.

### Example 8: Fiduciary Relationship
- **Ministry:** Ministry of Corporate Affairs
- **Section:** 8(1)(e)
- **Context:** I want information about complaints filed against a company. They denied under fiduciary relationship. But company is publicly listed and information is in public interest.

### Example 9: Law Enforcement
- **Ministry:** Ministry of Home Affairs
- **Section:** 8(1)(h)
- **Context:** I requested FIR copy of a case that was closed 5 years ago. PIO denied saying it would impede investigation. But case is already closed.

### Example 10: Tax Information
- **Ministry:** Income Tax Department
- **Section:** 8(1)(j)
- **Context:** I want details of tax assessments for my business. PIO denied saying it's confidential third party information. But I am requesting my own tax records.

---

## 3. Predict Outcome

**Note:** `appeal_level` indicates the stage of appeal:
- `first_appeal` - Appeal to First Appellate Authority (FAA) after PIO denial
- `second_appeal` - Appeal to Central Information Commission (CIC) after FAA decision

**Available Ministries in Database:**
- Income Tax Department
- Ministry of Corporate Affairs
- Ministry of Defence
- Ministry of Education
- Ministry of External Affairs
- Ministry of Finance
- Ministry of Home Affairs
- Ministry of Personnel, Public Grievances and Pensions
- Ministry of Railways

### Example 1: Strong Public Interest Case
- **Ministry:** Ministry of External Affairs
- **Section:** 8(1)(d)
- **Appeal Level:** second_appeal
- **Context:** Requesting environmental clearance documents for factory near residential area. Factory has history of pollution violations. Information needed for public health. PIO denied under commercial confidence. FAA upheld denial. Now appealing to CIC with evidence of public health risk.

### Example 2: Weak Security Claim
- **Ministry:** Ministry of Defence
- **Section:** 8(1)(a)
- **Appeal Level:** first_appeal
- **Context:** Requesting list of canteen contractors in army base. PIO denied citing national security. Only asking for contractor names and contract values, not strategic information. This is routine procurement information that should be public.

### Example 3: Legitimate Third Party Privacy
- **Ministry:** Ministry of Home Affairs
- **Section:** 8(1)(j)
- **Appeal Level:** first_appeal
- **Context:** Requesting medical records of another person without their consent. No public interest angle. Just personal curiosity about neighbor's health condition. PIO correctly denied under third party privacy exemption.

### Example 4: Completed Investigation
- **Ministry:** Ministry of Home Affairs
- **Section:** 8(1)(h)
- **Appeal Level:** second_appeal
- **Context:** Requesting investigation report of corruption case that was closed 3 years ago. All accused were acquitted. Information is now historical. PIO denied saying it would impede investigation. FAA upheld. But investigation is complete and case is closed.

### Example 5: Commercial Confidence - Ongoing
- **Ministry:** Ministry of Railways
- **Section:** 8(1)(d)
- **Appeal Level:** first_appeal
- **Context:** Requesting bid details of ongoing tender process. Tender evaluation is still in progress. Disclosure could affect fair competition. PIO denied under commercial confidence. This appears to be legitimate use of exemption.

### Example 6: Cabinet Papers - Recent
- **Ministry:** Ministry of Finance
- **Section:** 8(1)(i)
- **Appeal Level:** first_appeal
- **Context:** Requesting cabinet meeting minutes from last month about budget allocation. Decision-making process is still ongoing. PIO denied under cabinet papers exemption. Seeking information about deliberations that are not yet finalized.

### Example 7: Personal Information - Self
- **Ministry:** Ministry of Education
- **Section:** 8(1)(j)
- **Appeal Level:** first_appeal
- **Context:** Requesting my own academic records and evaluation sheets from university. This is my personal information and I have right to access it. PIO denied saying it's third party information of examiner. But I'm seeking my own records, not examiner's identity.

### Example 8: Delayed Response - No Exemption
- **Ministry:** Ministry of Personnel, Public Grievances and Pensions
- **Section:** NULL
- **Appeal Level:** first_appeal
- **Context:** Filed RTI 120 days ago asking for list of beneficiaries of government scheme in my village. PIO never responded. No exemption was cited. This is clear violation of RTI Act timelines. Seeking penalty on PIO and disclosure of information.

### Example 9: Public Interest Override
- **Ministry:** Ministry of Corporate Affairs
- **Section:** 8(1)(d)
- **Appeal Level:** second_appeal
- **Context:** Requesting inspection reports of pharmaceutical company that manufactures life-saving drugs. Recent reports of quality issues. Public health at stake. PIO denied under commercial confidence. FAA upheld. But public interest in drug safety outweighs commercial interests.

### Example 10: Vague Exemption Claim
- **Ministry:** Ministry of Home Affairs
- **Section:** 8(1)(a)
- **Appeal Level:** first_appeal
- **Context:** Requesting details of CCTV cameras installed in public areas of my neighborhood under smart city project. PIO denied saying it affects sovereignty and integrity of India. No clear explanation how public CCTV locations are security issue. This appears to be misuse of exemption.

---

## Tips for Testing

### RAG Q&A
- Try questions with different complexity levels
- Test both specific (section-based) and general questions
- Check if sources are cited correctly
- Verify confidence scores make sense

### Draft Generator
- Test with different section citations
- Try cases with and without section (delayed response)
- Check if improved query is actually better
- Verify sources are real CIC orders
- Look for specific legal language improvements

### Predict Outcome
- Test cases with clear public interest
- Test weak exemption claims
- Test legitimate privacy concerns
- Check if prediction reasoning makes sense
- Compare predictions with similar real cases

---

## Expected Behavior

### Good RAG Response
- Cites specific CIC orders
- Provides order numbers
- Explains legal reasoning
- High confidence for well-documented topics
- Lower confidence for edge cases

### Good Draft Output
- Improved query is more specific
- Identifies vague phrases in original
- Suggests concrete improvements
- References relevant precedents
- Provides phrases to avoid

### Good Prediction
- Clear outcome (allowed/denied/partial)
- Confidence score with reasoning
- Identifies key factors
- References similar cases
- Explains legal basis

---

## Notes

- All examples use real RTI Act sections
- Contexts are realistic scenarios
- Ministries are actual Indian government ministries
- Test with variations of these inputs
- Check consistency across multiple runs
