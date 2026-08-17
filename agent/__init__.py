"""Agent de surveillance anti-typosquatting.

Génère des variantes typosquattées d'un domaine, vérifie lesquelles sont
actives (DNS/WHOIS/certificat), fait trier les nouvelles détections par un
LLM (optionnel), puis envoie des alertes (email / Slack / Teams).
"""
