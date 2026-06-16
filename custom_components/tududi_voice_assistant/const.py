DOMAIN = "tududi_voice_assistant"
CONF_TUDUDI_URL = "tududi_url"
CONF_TUDUDI_API_KEY = "tududi_api_key"
CONF_AI_TASK_ENTITY = "ai_task_entity"
CONF_DUE_DATE = "default_due_date"
CONF_VOICE_CORRECTION = "voice_correction"
CONF_AUTO_VOICE_TAG = "auto_voice_tag"
DUE_DATE_OPTIONS = ["none", "tomorrow", "end_of_week", "end_of_month"]
CONF_DETAILED_RESPONSE = "detailed_response"
"""When true, detailed voice responses will include project, tags, due date, priority and recurrence info."""


DUE_DATE_OPTION_LABELS = {
    "none": {
        "en": "No default",
        "fr": "Aucun",
        "es": "Sin predeterminado",
        "pt": "Sem padrão",
        "ru": "Нет по умолчанию",
        "hi": "कोई डिफ़ॉल्ट नहीं",
        "zh-Hans": "无默认",
        "ar": "بدون افتراضي",
        "bn": "কোনো ডিফল্ট নয়",
        "id": "Tidak ada default",
        "de": "Kein Standard",
    },
    "tomorrow": {
        "en": "Tomorrow",
        "fr": "Demain",
        "es": "Mañana",
        "pt": "Amanhã",
        "ru": "Завтра",
        "hi": "कल",
        "zh-Hans": "明天",
        "ar": "غدًا",
        "bn": "আগামীকাল",
        "id": "Besok",
        "de": "Morgen",
    },
    "end_of_week": {
        "en": "End of week",
        "fr": "Fin de semaine",
        "es": "Fin de la semana",
        "pt": "Fim da semana",
        "ru": "Конец недели",
        "hi": "सप्ताह का अंत",
        "zh-Hans": "本周末",
        "ar": "نهاية الأسبوع",
        "bn": "সপ্তাহের শেষ",
        "id": "Akhir minggu",
        "de": "Ende der Woche",
    },
    "end_of_month": {
        "en": "End of month",
        "fr": "Fin du mois",
        "es": "Fin de mes",
        "pt": "Fim do mês",
        "ru": "Конец месяца",
        "hi": "महीने का अंत",
        "zh-Hans": "月底",
        "ar": "نهاية الشهر",
        "bn": "মাসের শেষ",
        "id": "Akhir bulan",
        "de": "Ende des Monats",
    },
}
