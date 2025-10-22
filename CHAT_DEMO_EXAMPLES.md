# Chat Demo - Real-World Examples

Complete examples of using the EMBM-J DS chat demo for spectrum management.

## Setup

```bash
# Terminal 1: Start MCP Server
python scripts/run_server.py

# Terminal 2: Start Chat Demo
python scripts/chat_demo.py
```

## Example 1: Simple Frequency Check

**Scenario**: You need to check if a frequency is available for a training exercise.

```
You: Is 151.5 MHz available for a training exercise?

Agent: I'll check if 151.5 MHz is available for your training exercise.
Let me query the spectrum plan and check for conflicts...

[Agent calls: get_spectrum_plan, request_deconfliction]

Agent: Good news! 151.5 MHz appears to be available in your area. 
The frequency is currently unallocated and has no known conflicts.

Would you like me to allocate this frequency for your training exercise?
I'll need:
- Asset ID
- Bandwidth requirement (typically 25 kHz)
- Power level
- Duration
- Location coordinates
```

## Example 2: Spectrum Planning Query

**Scenario**: You need to find available frequencies for multiple assets.

```
You: What frequencies are available for communications in the 150-230 MHz range?

Agent: I'll retrieve the spectrum plan for the 150-230 MHz range...

[Agent calls: get_spectrum_plan]

Agent: Here's the current spectrum allocation in the 150-230 MHz range:

Available Frequencies:
- 150.0-152.0 MHz: Available (25 kHz channels)
  * Suitable for: VHF communications, training
  * Capacity: 8 channels
  
- 225.0-230.0 MHz: Partially available
  * Available channels: 225.5, 226.0, 226.5 MHz
  * Occupied: 225.0, 226.0 MHz (military operations)
  * Recommendation: Use 225.5 or 226.5 MHz

- 230.0-235.0 MHz: Limited availability
  * Only 230.5 MHz available
  * High interference risk

Which frequency range interests you most?
```

## Example 3: Interference Analysis

**Scenario**: You want to understand interference conditions on a specific frequency.

```
You: I'm concerned about interference on 225 MHz. Can you analyze it?

Agent: I'll perform a detailed interference analysis on 225 MHz...

[Agent calls: get_interference_report]

Agent: Interference Analysis for 225 MHz:

Current Status:
- Signal-to-Noise Ratio: Good (18 dB)
- Active Emitters: 2 detected
- Potential Interference Sources: 1 identified
- Overall Assessment: Suitable for operations

Detailed Breakdown:
1. Primary User: Military radar (225.0 MHz)
   - Power: 45 dBm
   - Distance: ~50 km
   - Impact: Minimal at your location

2. Secondary User: Commercial aviation (225.5 MHz)
   - Power: 35 dBm
   - Distance: ~30 km
   - Impact: Low

3. Potential Interference: Unknown emitter (225.2 MHz)
   - Power: Unknown
   - Distance: Unknown
   - Impact: Requires investigation

Recommendation: 225.5 MHz is suitable with proper power management.
Would you like me to request deconfliction for this frequency?
```

## Example 4: Frequency Allocation Request

**Scenario**: You want to allocate a frequency for an ISR collection mission.

```
You: I need to allocate 151.5 MHz for ISR collection. Asset ID is ISR-001.

Agent: I'll help you allocate 151.5 MHz for ISR collection. 
Let me request deconfliction first...

[Agent calls: request_deconfliction]

Agent: Deconfliction request submitted for 151.5 MHz.

Deconfliction Results:
- Status: APPROVED
- Frequency: 151.5 MHz
- Bandwidth: 25 kHz
- Power: 35 dBm (recommended)
- Duration: 2 hours
- Location: Your specified area

Now I'll allocate the frequency...

[Agent calls: allocate_frequency]

Agent: ✅ Frequency Allocation Successful!

Allocation Details:
- Asset ID: ISR-001
- Frequency: 151.5 MHz
- Bandwidth: 25 kHz
- Power: 35 dBm
- Start Time: [Current time + 1 hour]
- Duration: 2 hours
- Authorization ID: AUTH-2025-001
- Status: ACTIVE

Your ISR collection mission is authorized to use 151.5 MHz.
Maintain power levels as specified to avoid interference.
```

## Example 5: Multi-turn Conversation

**Scenario**: Complex spectrum planning with follow-up questions.

```
You: What's the best frequency for a joint training exercise?

Agent: I'll help you find the best frequency for a joint training exercise.
Let me analyze the current spectrum...

[Agent calls: get_spectrum_plan]

Agent: For a joint training exercise, I recommend:

Top Recommendations:
1. 151.5 MHz - Best option
   - Availability: Excellent
   - Interference: None detected
   - Capacity: Supports multiple units
   - Recommendation: HIGHLY RECOMMENDED

2. 152.0 MHz - Good alternative
   - Availability: Good
   - Interference: Low
   - Capacity: Supports multiple units

3. 226.0 MHz - Acceptable
   - Availability: Fair
   - Interference: Moderate
   - Capacity: Limited

I recommend 151.5 MHz. Would you like me to allocate it?

---

You: How many units can use 151.5 MHz simultaneously?

Agent: Great question! For 151.5 MHz with 25 kHz bandwidth:

Capacity Analysis:
- Bandwidth: 25 kHz (standard for training)
- Frequency Range: 151.5 MHz ± 12.5 kHz
- Simultaneous Users: Up to 4 units
  * Each unit gets dedicated time slot
  * Or frequency-hopping for more units
  * Or wider bandwidth for fewer units

For your training exercise:
- 4 units: Standard configuration (recommended)
- 8 units: Requires frequency hopping
- 2 units: Allows wider bandwidth (50 kHz)

How many units will participate?

---

You: We have 6 units. What do you recommend?

Agent: For 6 units on 151.5 MHz, I recommend:

Option 1: Frequency Hopping (RECOMMENDED)
- Allows all 6 units to share 151.5 MHz
- Requires compatible radios
- Provides good spectrum efficiency
- Minimal interference risk

Option 2: Split Frequencies
- 151.5 MHz: 3 units
- 152.0 MHz: 3 units
- Simpler implementation
- Requires two allocations

Option 3: Wider Bandwidth
- 151.25-151.75 MHz: All 6 units
- Requires 50 kHz allocation
- May conflict with other users

I recommend Option 1 (Frequency Hopping) for your training exercise.
Shall I proceed with the allocation?

---

You: Yes, allocate 151.5 MHz for 6 units with frequency hopping.

Agent: Perfect! I'll allocate 151.5 MHz for 6 units with frequency hopping...

[Agent calls: request_deconfliction, allocate_frequency]

Agent: ✅ Allocation Complete!

Training Exercise Allocation:
- Primary Frequency: 151.5 MHz
- Mode: Frequency Hopping
- Units: 6
- Bandwidth: 25 kHz (per unit)
- Power: 35 dBm
- Duration: 4 hours
- Authorization ID: AUTH-2025-002
- Status: ACTIVE

All 6 units are authorized to use 151.5 MHz with frequency hopping.
Ensure all radios are configured for the hopping pattern.
```

## Example 6: Emergency Frequency Request

**Scenario**: Urgent frequency needed for emergency operations.

```
You: URGENT: I need a frequency immediately for emergency operations!

Agent: I understand this is urgent. Let me find an available frequency 
immediately...

[Agent calls: get_spectrum_plan, request_deconfliction]

Agent: ⚠️ EMERGENCY FREQUENCY ALLOCATION

Available Frequencies (Immediate):
1. 151.5 MHz - AVAILABLE NOW
   - Status: Clear
   - Interference: None
   - Recommended: YES

2. 152.0 MHz - AVAILABLE NOW
   - Status: Clear
   - Interference: None

3. 226.0 MHz - AVAILABLE NOW
   - Status: Clear
   - Interference: Low

Allocating 151.5 MHz for emergency operations...

[Agent calls: allocate_frequency]

Agent: ✅ EMERGENCY ALLOCATION APPROVED

Frequency: 151.5 MHz
Status: ACTIVE IMMEDIATELY
Authorization: EMERGENCY-2025-001
Duration: 4 hours (renewable)
Power: 40 dBm (emergency level)

Your emergency operations are authorized on 151.5 MHz.
Maintain situational awareness for other users.
```

## Example 7: Troubleshooting Interference

**Scenario**: Experiencing interference and need help.

```
You: We're experiencing interference on 225 MHz. What should we do?

Agent: I'll analyze the interference situation on 225 MHz...

[Agent calls: get_interference_report]

Agent: Interference Analysis for 225 MHz:

Current Interference Status:
- Signal Quality: DEGRADED
- Interference Level: HIGH
- Primary Cause: Unknown emitter at 225.2 MHz
- Recommendation: CHANGE FREQUENCY

Recommended Actions:
1. IMMEDIATE: Switch to 226.0 MHz (clear)
2. INVESTIGATE: Report unknown emitter
3. COORDINATE: Notify other users on 225 MHz

Alternative Frequencies:
- 226.0 MHz: Clear (RECOMMENDED)
- 226.5 MHz: Clear
- 151.5 MHz: Clear

Shall I allocate 226.0 MHz for your operations?

---

You: Yes, switch us to 226.0 MHz.

Agent: I'll deallocate 225 MHz and allocate 226.0 MHz...

[Agent calls: allocate_frequency]

Agent: ✅ Frequency Change Complete

Old Allocation: 225.0 MHz (DEALLOCATED)
New Allocation: 226.0 MHz (ACTIVE)
Authorization: AUTH-2025-003
Status: OPERATIONAL

You're now on 226.0 MHz with clear conditions.
Interference should be resolved.
```

## Tips for Best Results

1. **Be Specific**: Include asset IDs, locations, and durations
2. **Ask Follow-ups**: Build on previous responses
3. **Use Commands**: Type `help` for available commands
4. **Check History**: Use `history` to review conversation
5. **Watch Logs**: See MCP tool calls in terminal output

## Common Patterns

| Pattern | Example |
|---------|---------|
| **Availability Check** | "Is X MHz available?" |
| **Spectrum Planning** | "What frequencies are available?" |
| **Interference Analysis** | "Check interference on X MHz" |
| **Allocation Request** | "Allocate X MHz for Y" |
| **Emergency** | "URGENT: Need frequency now" |
| **Troubleshooting** | "We have interference on X MHz" |

---

**Ready to try?** Run `python scripts/chat_demo.py` and start chatting! 🚀

