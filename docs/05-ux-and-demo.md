# UX specification & demo script

## Design system

- Primary `#0F3D3E` (utility teal)
- Accent `#F4A261`
- Critical `#E63946`
- Surface warm off-white `#F4F1EC`
- Risk colors: green / amber / orange / red

Typography: Source Sans 3. Cards, not chrome. Field users wear gloves; tap targets are large.

## Screens

| # | Screen | States |
|---|--------|--------|
| 1 | Splash | Bootstrapping session |
| 2 | Login | Busy, invalid credentials, offline demo fallback, custom API URL |
| 3 | Dashboard | KPI cards, wow-path shortcut, offline banner |
| 4 | Asset map | Filter all/critical/high/medium/low, marker tap |
| 5 | Asset list | Search |
| 6 | Asset details | Risk, history, start inspection |
| 7–11 | Inspection form | Temperature, leakage, noise, damage, notes, photo, live risk preview |
| 12 | AI + risk result | Breakdown + insight + fallback copy |
| 13 | Inspection list | Status + sync badge |
| 14 | Work orders | Priority badge, empty state |
| 15 | Analytics | KPIs + pie + categories |
| 16 | Notifications | Inbox |
| 17 | Profile / more | Role, security note |
| 18 | Settings | API URL on login |
| 19–20 | Offline queue / sync | Pending count, human error copy |

Empty, loading, error, and offline copy is specific:

- *No internet — your inspection is saved locally. It will synchronize automatically when connectivity returns.*
- *AI analysis temporarily unavailable. Your inspection has been saved.*
- *Unable to synchronize. Your data remains safely stored on this device.*

## Navigation

Bottom destinations: Home, Map, Assets, Work, More.

## Demo script (do not click around randomly)

**Say:** “Imagine I am an electrical field inspector for Helios Grid.”

1. Login as inspector  
2. Map → T-104 (Midrand)  
3. Start inspection  
4. Leave defaults (91°C, oil yes, noise high, damage yes) — they are the story  
5. Submit  
6. Show **87-class CRITICAL** from rules, then AI insight  
7. Work orders: follow-up created  
8. Analytics: critical +1, open work +1  

That is a coherent product, not a gallery of screens.
