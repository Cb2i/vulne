# Diagramme des workflows

## 1. Diagramme global (Mermaid)

```mermaid
flowchart TD
    CRON["Schedule Trigger\n00:00 / 08:00 / 16:00\nAmerica/Toronto"] --> WF01

    subgraph WF01["WF01_JOB_DISCOVERY"]
        S1[APIs officielles / RSS / alertes courriel / pages carrière / ATS publics]
    end

    WF01 -->|jobs bruts par source| WF02

    subgraph WF02["WF02_JOB_NORMALIZER"]
        N1[Mapping vers schéma JSON commun]
    end

    WF02 --> WF03

    subgraph WF03["WF03_DEDUPLICATION"]
        D1[Fingerprint SHA256]
        D2{NEW / DUPLICATE /\nALREADY_APPLIED /\nUPDATED_JOB ?}
        D1 --> D2
    end

    WF03 -->|NEW / UPDATED_JOB| WF04
    WF03 -->|DUPLICATE / ALREADY_APPLIED| STOP1[Log + Stop]

    subgraph WF04["WF04_AI_JOB_ANALYZER"]
        A1[Claude JOB_ANALYZER]
        A2{overall_score >= 70 ?}
        A3[OpenAI Reviewer]
        A4{écart > 10 pts ?}
        A5[Claude - 2e analyse]
        A6[Score consolidé]
        A1 --> A2
        A2 -->|oui| A3 --> A4
        A4 -->|oui| A5 --> A6
        A4 -->|non| A6
        A2 -->|non| A6
    end

    WF04 --> DEC{Classification}
    DEC -->|0-59 REJECT| REJ[Airtable: REJECTED + raison]
    DEC -->|60-69 MANUAL_REVIEW| MR[Airtable: REQUIRES_MANUAL_REVIEW\n+ inclus au rapport]
    DEC -->|70-100 APPLY / PRIORITY| WF05

    subgraph WF05["WF05_COMPANY_RESEARCH"]
        C1[Claude COMPANY_RESEARCHER]
    end

    WF05 --> WF06

    subgraph WF06["WF06_CV_OPTIMIZER"]
        O1[Sélection CV FR/EN]
        O2[Analyse mots-clés / écarts]
        O3[Adaptation CV - faits vérifiés uniquement]
        O4[Recalcul ATS_MATCH]
        O5{ATS_MATCH >= 80 ?}
        O1 --> O2 --> O3 --> O4 --> O5
        O5 -->|non, iterations restantes| O3
    end

    WF06 --> WF07

    subgraph WF07["WF07_CV_GENERATOR"]
        G1[Génération PDF CV]
        G2{Lettre requise ?}
        G3[Génération lettre de motivation]
        G4[Stockage OneDrive/SharePoint]
        G1 --> G2
        G2 -->|oui| G3 --> G4
        G2 -->|non| G4
    end

    WF07 --> WF08

    subgraph WF08["WF08_APPLICATION_AGENT"]
        P1{Règle §30 respectée ?\nscore/ats/blocages/quota/\ncaptcha/questions inconnues}
        P2[Réponses aux questions standards]
        P3{Automatisation permise\nsur cette plateforme ?}
        P4[Soumission automatique]
        P5[BLOCKED_REQUIRES_MANUAL_ACTION]
        P1 -->|oui| P2 --> P3
        P3 -->|oui, pas de CAPTCHA/MFA| P4
        P3 -->|non| P5
        P1 -->|non| P5
    end

    WF08 --> WF09

    subgraph WF09["WF09_APPLICATION_TRACKER"]
        T1[Update Airtable]
        T2[Sync Excel 365]
        T3{overall_score >= 90 ?}
        T4[Email notification immédiate]
        T1 --> T2 --> T3
        T3 -->|oui| T4
    end

    WF09 --> DONE1[Fin de cycle]

    CRON2["Schedule Trigger\ntoutes les 30-60 min"] --> WF10

    subgraph WF10["WF10_EMAIL_RESPONSE_MONITOR"]
        E1[Lecture boîte Outlook]
        E2[Claude classification courriel]
        E3[Extraction entités]
        E4[Update Airtable statut]
        E1 --> E2 --> E3 --> E4
    end

    CRON3["Schedule Trigger\nfin de journée (ex: 22:00)"] --> WF11

    subgraph WF11["WF11_DAILY_REPORT"]
        R1[Agrégation Airtable]
        R2[Calcul métriques]
        R3[Génération HTML email]
        R4[Envoi Outlook]
        R1 --> R2 --> R3 --> R4
    end

    ERR["WF12_ERROR_HANDLER\n(appelé par tous les workflows\nvia Error Trigger / Execute Workflow)"]
    WF01 -.erreur.-> ERR
    WF02 -.erreur.-> ERR
    WF03 -.erreur.-> ERR
    WF04 -.erreur.-> ERR
    WF05 -.erreur.-> ERR
    WF06 -.erreur.-> ERR
    WF07 -.erreur.-> ERR
    WF08 -.erreur.-> ERR
    WF09 -.erreur.-> ERR
    WF10 -.erreur.-> ERR
    WF11 -.erreur.-> ERR
```

## 2. Table de correspondance workflow ↔ déclencheur

| Workflow | Déclencheur | Fréquence |
|---|---|---|
| WF01_JOB_DISCOVERY | Schedule Trigger | 00:00, 08:00, 16:00 America/Toronto |
| WF02_JOB_NORMALIZER | Execute Workflow (appelé par WF01) | à chaque exécution WF01 |
| WF03_DEDUPLICATION | Execute Workflow (appelé par WF02) | à chaque exécution WF02 |
| WF04_AI_JOB_ANALYZER | Execute Workflow (appelé par WF03, offres NEW/UPDATED_JOB) | à chaque offre |
| WF05_COMPANY_RESEARCH | Execute Workflow (appelé par WF04, score ≥70) | à chaque offre qualifiée |
| WF06_CV_OPTIMIZER | Execute Workflow (appelé par WF05) | à chaque offre qualifiée |
| WF07_CV_GENERATOR | Execute Workflow (appelé par WF06) | à chaque offre qualifiée |
| WF08_APPLICATION_AGENT | Execute Workflow (appelé par WF07) | à chaque offre qualifiée |
| WF09_APPLICATION_TRACKER | Execute Workflow (appelé par WF08) | à chaque candidature/blocage |
| WF10_EMAIL_RESPONSE_MONITOR | Schedule Trigger | toutes les 30-60 min |
| WF11_DAILY_REPORT | Schedule Trigger | 1x/jour, ex. 22:00 America/Toronto |
| WF12_ERROR_HANDLER | Error Trigger / Execute Workflow (sous-workflow) | sur erreur, depuis n'importe quel workflow |

## 3. Convention d'appel entre workflows

Tous les appels inter-workflows utilisent le node **Execute Workflow** (mode "Define below" avec
l'ID du workflow cible, ou "From list") et passent un objet JSON unique par item en entrée/sortie,
conforme au schéma commun (§15 du prompt utilisateur). Chaque sous-workflow commence par un node
**Execute Workflow Trigger** et retourne son résultat via un node **NoOp** nommé
`Return_To_Caller` (dernier node), afin que le workflow appelant reçoive directement les données.
