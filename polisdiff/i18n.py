"""Reviewed interface wording only. PDF and official legal quotations are never translated."""
from string import Formatter
import re

LANGUAGES = {"ru": "Русский", "uz-Latn": "O‘zbekcha", "uz-Cyrl": "Ўзбекча (кирилл)", "en": "English"}
HTML_LANGUAGES = {"ru": "ru", "uz-Latn": "uz-Latn", "uz-Cyrl": "uz-Cyrl", "en": "en"}

# Russian is the existing default. Rows are Russian, English, Uzbek Latin, Uzbek Cyrillic.
ROWS = [
    ("Предварительная проверка ОСАГО · Узбекистан", "Preliminary OSAGO review · Uzbekistan", "OSAGO bo‘yicha dastlabki tekshiruv · O‘zbekiston", "ОСАГО бўйича дастлабки текширув · Ўзбекистон"),
    ("Три условия: общая сумма, срок выплаты и уведомление о решении.", "Three conditions: total insured amount, payment deadline and decision notification.", "Uchta shart: umumiy sug‘urta summasi, to‘lov muddati va qaror haqida xabarnoma.", "Учта шарт: умумий суғурта суммаси, тўлов муддати ва қарор ҳақида хабарнома."),
    ("Не юридическое заключение. Интерпретации ожидают проверки юристом: PENDING_LEGAL_REVIEW.", "Not a legal opinion. Interpretations await qualified legal review: PENDING_LEGAL_REVIEW.", "Bu huquqiy xulosa emas. Talqinlar malakali yurist tekshiruvini kutmoqda: PENDING_LEGAL_REVIEW.", "Бу ҳуқуқий хулоса эмас. Талқинлар малакали юрист текширувини кутмоқда: PENDING_LEGAL_REVIEW."),
    ("Анализ выполняется локально, без внешних AI API. PDF и аннотации хранятся в памяти сессии. Экспортируйте записи перед очисткой.", "Analysis runs locally without external AI APIs. PDFs and annotations stay in session memory. Export records before clearing.", "Tahlil tashqi AI API xizmatlarisiz, lokal bajariladi. PDF va izohlar sessiya xotirasida saqlanadi. Tozalashdan oldin yozuvlarni eksport qiling.", "Таҳлил ташқи AI API хизматларисиз, локал бажарилади. PDF ва изоҳлар сессия хотирасида сақланади. Тозалашдан олдин ёзувларни экспорт қилинг."),
    ("Очистить сессию", "Clear session", "Sessiyani tozalash", "Сессияни тозалаш"),
    ("POLISDIFF AI / ПРЕДВАРИТЕЛЬНАЯ ПРОВЕРКА", "POLISDIFF AI / PRELIMINARY REVIEW", "POLISDIFF AI / DASTLABKI TEKSHIRUV", "POLISDIFF AI / ДАСТЛАБКИ ТЕКШИРУВ"),
    ("Условия полиса, с доказательствами", "Policy conditions, with evidence", "Polis shartlari va dalillar", "Полис шартлари ва далиллар"),
    ("Найдите три ключевых условия ОСАГО, сравните их с критериями для выбранной даты и проверьте цитаты в оригинале.", "Find three key OSAGO conditions, compare them with the criteria for the selected date and check quotations in the original PDF.", "OSAGO bo‘yicha uchta asosiy shartni toping, tanlangan sana mezonlari bilan solishtiring va iqtiboslarni asl PDF hujjatida tekshiring.", "ОСАГО бўйича учта асосий шартни топинг, танланган сана мезонлари билан солиштиринг ва иқтибосларни асл PDF ҳужжатида текширинг."),
    ("Результат относится к отдельным условиям, а не ко всему договору. «Не найдено» не означает нарушение.", "Results cover individual conditions, not the entire contract. “Not found” does not mean a violation.", "Natija butun shartnomaga emas, alohida shartlarga tegishli. «Topilmadi» qonun buzilganini anglatmaydi.", "Натижа бутун шартномага эмас, алоҳида шартларга тегишли. «Топилмади» қонун бузилганини англатмайди."),
    ("1. Документ и даты", "1. Document and dates", "1. Hujjat va sanalar", "1. Ҳужжат ва саналар"),
    ("Загрузить PDF ОСАГО", "Upload OSAGO PDF", "OSAGO PDF hujjatini yuklash", "ОСАГО PDF ҳужжатини юклаш"),
    ("Текстовый PDF · до 10 МиБ · от 1 до 80 страниц. Русский, узбекская латиница и кириллица. Сканы без текстового слоя не поддерживаются: OCR отсутствует.", "Text-based PDF · up to 10 MiB · 1–80 pages. Russian, Uzbek Latin and Cyrillic documents. Image-only scans are unsupported: no OCR.", "Matnli PDF · 10 MiB gacha · 1–80 sahifa. Ruscha, o‘zbek lotin va kirill yozuvidagi hujjatlar. Matnsiz skanlar qo‘llab-quvvatlanmaydi: OCR mavjud emas.", "Матнли PDF · 10 MiB гача · 1–80 саҳифа. Русча, ўзбек лотин ва кирилл ёзувидаги ҳужжатлар. Матнсиз сканлар қўллаб-қувватланмайди: OCR мавжуд эмас."),
    ("Продукт ОСАГО выбран пользователем. Другие виды страхования не проверяются.", "OSAGO is selected by the user. Other insurance products are not checked.", "OSAGO mahsulotini foydalanuvchi tanlaydi. Boshqa sug‘urta turlari tekshirilmaydi.", "ОСАГО маҳсулотини фойдаланувчи танлайди. Бошқа суғурта турлари текширилмайди."),
    ("Когда применялся договор?", "When did the contract apply?", "Shartnoma qaysi sanaga tegishli?", "Шартнома қайси санага тегишли?"),
    ("Дата применимости — дата, для которой проверяются условия договора и редакция нормы. Установите ее по договору или оферте; дата загрузки и дата, найденная на странице, ее не заменяют.", "The applicability date selects the contract conditions and legal version being checked. Confirm it from the contract or offer; the upload date or a date found on a page does not replace it.", "Qo‘llanish sanasi shartnoma shartlari va norma tahriri qaysi sana uchun tekshirilishini belgilaydi. Uni shartnoma yoki ofertadan tasdiqlang; yuklash sanasi yoki sahifada topilgan sana uning o‘rnini bosmaydi.", "Қўлланиш санаси шартнома шартлари ва норма таҳрири қайси сана учун текширилишини белгилайди. Уни шартнома ёки офертадан тасдиқланг; юклаш санаси ёки саҳифада топилган сана унинг ўрнини босмайди."),
    ("Я подтверждаю дату применимости договора", "I confirm the contract applicability date", "Shartnomaning qo‘llanish sanasini tasdiqlayman", "Шартноманинг қўлланиш санасини тасдиқлайман"),
    ("Дата применимости договора", "Contract applicability date", "Shartnomaning qo‘llanish sanasi", "Шартноманинг қўлланиш санаси"),
    ("Дата аудита", "Audit date", "Tekshiruv sanasi", "Текширув санаси"),
    ("Дата аудита — когда выполняется проверка. Она не определяет, какая редакция нормы применима к договору.", "The audit date records when the review is performed. It does not select the legal version applicable to the contract.", "Tekshiruv sanasi tekshiruv qachon o‘tkazilishini ko‘rsatadi. U shartnomaga qaysi norma tahriri qo‘llanishini belgilamaydi.", "Текширув санаси текширув қачон ўтказилишини кўрсатади. У шартномага қайси норма таҳрири қўлланишини белгиламайди."),
    ("Дата договора неизвестна или не указана. Можно найти связанный текст, но все три числовые проверки останутся без вывода о соответствии.", "The contract date is unknown or missing. Related text can be found, but all three numerical checks will abstain from a consistency conclusion.", "Shartnoma sanasi noma’lum yoki kiritilmagan. Tegishli matn topilishi mumkin, ammo uchala sonli tekshiruv bo‘yicha moslik xulosasi berilmaydi.", "Шартнома санаси номаълум ёки киритилмаган. Тегишли матн топилиши мумкин, аммо учала сонли текширув бўйича мослик хулосаси берилмайди."),
    ("Дата вне подтвержденного диапазона каталога или позже даты аудита. Система воздержится от сравнения; проверьте даты и редакцию нормы.", "The date is outside the verified catalogue range or later than the audit date. The system will abstain; check the dates and legal version.", "Sana katalogning tasdiqlangan oralig‘idan tashqarida yoki tekshiruv sanasidan keyin. Tizim solishtirishdan tiyiladi; sanalar va norma tahririni tekshiring.", "Сана каталогнинг тасдиқланган оралиғидан ташқарида ёки текширув санасидан кейин. Тизим солиштиришдан тийилади; саналар ва норма таҳририни текширинг."),
    ("Дополнительные настройки поиска", "Advanced search settings", "Qidiruvning qo‘shimcha sozlamalari", "Қидирувнинг қўшимча созламалари"),
    ("Поиск доказательств", "Evidence search", "Dalillarni qidirish", "Далилларни қидириш"),
    ("AI + лексический поиск", "AI + lexical search", "AI + so‘zlar bo‘yicha qidiruv", "AI + сўзлар бўйича қидирув"),
    ("AI поиск", "AI search", "AI qidiruvi", "AI қидируви"),
    ("Лексический поиск", "Lexical search", "So‘zlar bo‘yicha qidiruv", "Сўзлар бўйича қидирув"),
    ("По умолчанию — локальная модель вместе с поиском по словам. Малый тестовый набор не устанавливает преимущество AI в точности. При отсутствии модели используется явно обозначенный поиск по словам.", "The default combines a local model with lexical search. The small test set does not establish an AI accuracy advantage. If the model is unavailable, lexical fallback is explicitly shown.", "Standart rejim lokal modelni so‘zlar bo‘yicha qidiruv bilan birlashtiradi. Kichik test to‘plami AI aniqligi ustunligini isbotlamaydi. Model mavjud bo‘lmasa, so‘zlar bo‘yicha qidiruvga o‘tish ochiq ko‘rsatiladi.", "Стандарт режим локал моделни сўзлар бўйича қидирув билан бирлаштиради. Кичик тест тўплами AI аниқлиги устунлигини исботламайди. Модель мавжуд бўлмаса, сўзлар бўйича қидирувга ўтиш очиқ кўрсатилади."),
    ("Анализировать документ", "Analyze document", "Hujjatni tahlil qilish", "Ҳужжатни таҳлил қилиш"),
    ("Подождите пять секунд между анализами.", "Wait five seconds between analyses.", "Tahlillar orasida besh soniya kuting.", "Таҳлиллар орасида беш сония кутинг."),
    ("Подготовка локального поиска…", "Preparing local search…", "Lokal qidiruv tayyorlanmoqda…", "Локал қидирув тайёрланмоқда…"),
    ("Читаем документ в отдельном процессе", "Reading the document in an isolated process", "Hujjat alohida jarayonda o‘qilmoqda", "Ҳужжат алоҳида жараёнда ўқилмоқда"),
    ("Ищем относящиеся к проверкам положения", "Finding provisions relevant to the checks", "Tekshiruvlarga tegishli bandlar qidirilmoqda", "Текширувларга тегишли бандлар қидирилмоқда"),
    ("Проверяем три выбранных условия", "Checking the three selected conditions", "Tanlangan uchta shart tekshirilmoqda", "Танланган учта шарт текширилмоқда"),
    ("Готовим отчет и ссылки на доказательства", "Preparing the report and evidence references", "Hisobot va dalillarga havolalar tayyorlanmoqda", "Ҳисобот ва далилларга ҳаволалар тайёрланмоқда"),
    ("Проверка завершена", "Review complete", "Tekshiruv tugadi", "Текширув тугади"),
    ("PDF не удалось прочитать безопасно: проверьте формат, шифрование, размер и число страниц. Это проблема обработки файла, а не вывод об условиях договора.", "The PDF could not be read safely: check its format, encryption, size and page count. This is a file-processing problem, not a conclusion about the contract.", "PDF xavfsiz o‘qilmadi: format, shifrlash, hajm va sahifalar sonini tekshiring. Bu faylni qayta ishlash muammosi, shartnoma haqida xulosa emas.", "PDF хавфсиз ўқилмади: формат, шифрлаш, ҳажм ва саҳифалар сонини текширинг. Бу файлни қайта ишлаш муаммоси, шартнома ҳақида хулоса эмас."),
    ("Сервер сейчас выполняет другой анализ. Повторите запрос после его завершения.", "The server is analyzing another document. Retry when it finishes.", "Server boshqa hujjatni tahlil qilmoqda. U tugagach qayta urinib ko‘ring.", "Сервер бошқа ҳужжатни таҳлил қилмоқда. У тугагач қайта уриниб кўринг."),
    ("Обработка не завершена; отчет не создан. Попробуйте поиск по словам или другой текстовый PDF. Это не означает нарушение в договоре.", "Processing did not finish; no report was created. Try lexical search or another text-based PDF. This does not mean a contract violation.", "Qayta ishlash tugamadi; hisobot yaratilmadi. So‘zlar bo‘yicha qidiruvni yoki boshqa matnli PDF hujjatini sinang. Bu shartnomada qonun buzilganini anglatmaydi.", "Қайта ишлаш тугамади; ҳисобот яратилмади. Сўзлар бўйича қидирувни ёки бошқа матнли PDF ҳужжатини синанг. Бу шартномада қонун бузилганини англатмайди."),
    ("Страница PDF {page} · {section} · {readability}", "PDF page {page} · {section} · {readability}", "PDF sahifasi {page} · {section} · {readability}", "PDF саҳифаси {page} · {section} · {readability}"),
    ("текст читается", "readable text", "matn o‘qiladi", "матн ўқилади"),
    ("текст поврежден или отсутствует", "damaged or missing text", "matn buzilgan yoki yo‘q", "матн бузилган ёки йўқ"),
    ("Цитата выбранной находки", "Selected finding quotation", "Tanlangan topilma iqtibosi", "Танланган топилма иқтибоси"),
    ("Изображение страницы недоступно. Проверьте оригинальный PDF.", "The page image is unavailable. Check the original PDF.", "Sahifa tasviri mavjud emas. Asl PDF hujjatini tekshiring.", "Саҳифа тасвири мавжуд эмас. Асл PDF ҳужжатини текширинг."),
    ("Исходный текст страницы", "Original page text", "Sahifaning asl matni", "Саҳифанинг асл матни"),
    ("Текстовый слой отсутствует", "No text layer", "Matn qatlami yo‘q", "Матн қатлами йўқ"),
    ("Цитаты сохранены без перевода. Координаты объединяют блоки текста и недостаточно точны для выделения цитаты; показана правильная страница без ложной подсветки.", "Quotations remain untranslated. Coordinates combine text blocks and are too coarse for exact highlighting; the correct page is shown without misleading highlights.", "Iqtiboslar tarjima qilinmagan. Koordinatalar matn bloklarini birlashtiradi va aniq ajratish uchun yetarli emas; to‘g‘ri sahifa noto‘g‘ri belgilashsiz ko‘rsatiladi.", "Иқтибослар таржима қилинмаган. Координаталар матн блокларини бирлаштиради ва аниқ ажратиш учун етарли эмас; тўғри саҳифа нотўғри белгилашсиз кўрсатилади."),
    ("2. Краткий итог", "2. Summary", "2. Qisqa xulosa", "2. Қисқа хулоса"),
    ("Документ: {name} · страниц: {pages} · {languages}", "Document: {name} · pages: {pages} · {languages}", "Hujjat: {name} · sahifalar: {pages} · {languages}", "Ҳужжат: {name} · саҳифалар: {pages} · {languages}"),
    ("Дата договора: {applicable} · дата аудита: {audit} · проверок: {checks}", "Contract date: {applicable} · audit date: {audit} · checks: {checks}", "Shartnoma sanasi: {applicable} · tekshiruv sanasi: {audit} · tekshiruvlar: {checks}", "Шартнома санаси: {applicable} · текширув санаси: {audit} · текширувлар: {checks}"),
    ("не подтверждена", "not confirmed", "tasdiqlanmagan", "тасдиқланмаган"),
    ("Согласуются с критерием", "Consistent with criterion", "Mezonga mos", "Мезонга мос"),
    ("Возможные несоответствия", "Possible inconsistencies", "Ehtimoliy nomuvofiqliklar", "Эҳтимолий номувофиқликлар"),
    ("Не найдены", "Not found", "Topilmadi", "Топилмади"),
    ("Недостаточно данных", "Insufficient information", "Ma’lumot yetarli emas", "Маълумот етарли эмас"),
    ("AI-модель недоступна. Анализ выполнен поиском по словам, без AI. Фактический режим указан в отчете.", "The AI model is unavailable. Analysis used lexical search without AI. The actual mode is recorded in the report.", "AI modeli mavjud emas. Tahlil AI siz, so‘zlar bo‘yicha qidiruv bilan bajarildi. Haqiqiy rejim hisobotda ko‘rsatilgan.", "AI модели мавжуд эмас. Таҳлил AI сиз, сўзлар бўйича қидирув билан бажарилди. Ҳақиқий режим ҳисоботда кўрсатилган."),
    ("Фактический поиск: {mode}", "Actual search: {mode}", "Haqiqiy qidiruv: {mode}", "Ҳақиқий қидирув: {mode}"),
    ("Проблема обработки: текст не читается надежно на страницах {pages}. Это ограничение PDF, а не страхового условия.", "Processing issue: text cannot be read reliably on pages {pages}. This is a PDF limitation, not an insurance-condition concern.", "Qayta ishlash muammosi: {pages} sahifalarda matn ishonchli o‘qilmaydi. Bu sug‘urta shartining emas, PDF hujjatining cheklovi.", "Қайта ишлаш муаммоси: {pages} саҳифаларда матн ишончли ўқилмайди. Бу суғурта шартининг эмас, PDF ҳужжатининг чеклови."),
    ("Найденные на первой странице даты — только подсказки: {dates}", "Dates found on the first page are hints only: {dates}", "Birinchi sahifada topilgan sanalar faqat yordamchi ma’lumot: {dates}", "Биринчи саҳифада топилган саналар фақат ёрдамчи маълумот: {dates}"),
    ("Только три условия; полнота поиска не гарантируется. Все интерпретации: PENDING_LEGAL_REVIEW.", "Only three conditions; search completeness is not guaranteed. All interpretations: PENDING_LEGAL_REVIEW.", "Faqat uchta shart; qidiruv to‘liqligi kafolatlanmaydi. Barcha talqinlar: PENDING_LEGAL_REVIEW.", "Фақат учта шарт; қидирув тўлиқлиги кафолатланмайди. Барча талқинлар: PENDING_LEGAL_REVIEW."),
    ("Результаты", "Findings", "Natijalar", "Натижалар"),
    ("Доказательства документа", "Document evidence", "Hujjat dalillari", "Ҳужжат далиллари"),
    ("Решение аналитика", "Analyst review", "Tahlilchi qarori", "Таҳлилчи қарори"),
    ("Источники и ограничения", "Sources and limitations", "Manbalar va cheklovlar", "Манбалар ва чекловлар"),
    ("Что проверяли", "What we checked", "Nima tekshirildi", "Нима текширилди"),
    ("Что найдено", "What we found", "Nima topildi", "Нима топилди"),
    ("Почему получен результат", "Why this result appeared", "Natijaning sababi", "Натижанинг сабаби"),
    ("Ориентир для выбранной даты", "Reference for the selected date", "Tanlangan sana uchun mezon", "Танланган сана учун мезон"),
    ("Официальный источник · LexUZ", "Official source · LexUZ", "Rasmiy manba · LexUZ", "Расмий манба · LexUZ"),
    ("Доказательства", "Evidence", "Dalillar", "Далиллар"),
    ("Подходящее доказательство не найдено. Цитата и страница отсутствуют.", "No qualifying evidence was located. No quotation or page is available.", "Mos dalil topilmadi. Iqtibos va sahifa mavjud emas.", "Мос далил топилмади. Иқтибос ва саҳифа мавжуд эмас."),
    ("Страница PDF {page}", "PDF page {page}", "PDF sahifasi {page}", "PDF саҳифаси {page}"),
    ("Посмотреть доказательство · стр. {page}", "View evidence · page {page}", "Dalilni ko‘rish · sahifa {page}", "Далилни кўриш · саҳифа {page}"),
    ("Выбранное доказательство в PDF", "Selected evidence in PDF", "PDF hujjatidagi tanlangan dalil", "PDF ҳужжатидаги танланган далил"),
    ("Следующий шаг", "Next step", "Keyingi qadam", "Кейинги қадам"),
    ("Аннотация аналитика: {action} · {timestamp}", "Analyst annotation: {action} · {timestamp}", "Tahlilchi izohi: {action} · {timestamp}", "Таҳлилчи изоҳи: {action} · {timestamp}"),
    ("Технические детали · ", "Technical details · ", "Texnik tafsilotlar · ", "Техник тафсилотлар · "),
    ("Запрошено: {requested}; выполнено: {used}", "Requested: {requested}; used: {used}", "So‘ralgan: {requested}; bajarilgan: {used}", "Сўралган: {requested}; бажарилган: {used}"),
    ("Сохранить отчет", "Save report", "Hisobotni saqlash", "Ҳисоботни сақлаш"),
    ("HTML — читаемый отчет с цитатами и аннотациями. Для PDF откройте HTML и выберите «Печать → Сохранить как PDF». JSON сохраняет исходные статусы и метаданные.", "HTML is a readable report with quotations and annotations. For PDF, open HTML and choose “Print → Save as PDF”. JSON preserves original statuses and metadata.", "HTML — iqtibos va izohlar bilan o‘qishga qulay hisobot. PDF uchun HTML hujjatini ochib, «Chop etish → PDF sifatida saqlash»ni tanlang. JSON asl holatlar va metama’lumotlarni saqlaydi.", "HTML — иқтибос ва изоҳлар билан ўқишга қулай ҳисобот. PDF учун HTML ҳужжатини очиб, «Чоп этиш → PDF сифатида сақлаш»ни танланг. JSON асл ҳолатлар ва метамаълумотларни сақлайди."),
    ("Скачать JSON отчет", "Download JSON report", "JSON hisobotini yuklab olish", "JSON ҳисоботини юклаб олиш"),
    ("Скачать HTML отчет", "Download HTML report", "HTML hisobotini yuklab olish", "HTML ҳисоботини юклаб олиш"),
    ("Исходный документ", "Original document", "Asl hujjat", "Асл ҳужжат"),
    ("Страница документа", "Document page", "Hujjat sahifasi", "Ҳужжат саҳифаси"),
    ("Номер страницы", "Page number", "Sahifa raqami", "Саҳифа рақами"),
    ("Показать изображение страницы", "Show page image", "Sahifa tasvirini ko‘rsatish", "Саҳифа тасвирини кўрсатиш"),
    ("Аннотация аналитика", "Analyst annotation", "Tahlilchi izohi", "Таҳлилчи изоҳи"),
    ("Запись не меняет результат алгоритма и не является юридической сертификацией. Она хранится в этой сессии; экспортируйте ее перед очисткой.", "The annotation does not change the algorithm's result and is not legal certification. It stays in this session; export it before clearing.", "Izoh algoritm natijasini o‘zgartirmaydi va huquqiy sertifikat emas. U shu sessiyada saqlanadi; tozalashdan oldin eksport qiling.", "Изоҳ алгоритм натижасини ўзгартирмайди ва ҳуқуқий сертификат эмас. У шу сессияда сақланади; тозалашдан олдин экспорт қилинг."),
    ("Проверка", "Rule", "Tekshiruv", "Текширув"),
    ("Действие", "Action", "Amal", "Амал"),
    ("Обоснование", "Rationale", "Asos", "Асос"),
    ("Записать решение", "Record review", "Qarorni yozish", "Қарорни ёзиш"),
    ("Укажите обоснование длиной от 3 до 2000 символов.", "Enter a rationale of 3–2000 characters.", "3–2000 belgidan iborat asos kiriting.", "3–2000 белгидан иборат асос киритинг."),
    ("Каталог {version} · подтвержденный диапазон: {dates}", "Catalogue {version} · verified range: {dates}", "Katalog {version} · tasdiqlangan oraliq: {dates}", "Каталог {version} · тасдиқланган оралиқ: {dates}"),
    ("Предупреждения и метаданные анализа", "Analysis warnings and metadata", "Tahlil ogohlantirishlari va metama’lumotlari", "Таҳлил огоҳлантиришлари ва метамаълумотлари"),
    ("Загрузите документ, установите даты и запустите проверку. При изменении файла, даты или поиска прежний результат и аннотации удаляются из текущей сессии.", "Upload a document, set dates and run the review. Changing the file, dates or search mode clears the previous result and annotations from this session.", "Hujjatni yuklang, sanalarni belgilang va tekshiruvni boshlang. Fayl, sana yoki qidiruv rejimi o‘zgarsa, oldingi natija va izohlar shu sessiyadan o‘chiriladi.", "Ҳужжатни юкланг, саналарни белгиланг ва текширувни бошланг. Файл, сана ёки қидирув режими ўзгарса, олдинги натижа ва изоҳлар шу сессиядан ўчирилади."),
    ("Условие согласуется с проверяемым критерием", "Condition consistent with the checked criterion", "Shart tekshirilgan mezonga mos", "Шарт текширилган мезонга мос"),
    ("Возможное несоответствие — нужна проверка", "Possible inconsistency — review required", "Ehtimoliy nomuvofiqlik — tekshiruv zarur", "Эҳтимолий номувофиқлик — текширув зарур"),
    ("Условие не найдено в проверенном тексте", "Relevant condition not found in the analyzed text", "Tegishli shart tekshirilgan matnda topilmadi", "Тегишли шарт текширилган матнда топилмади"),
    ("Недостаточно данных для проверки", "Insufficient information to verify", "Tekshirish uchun ma’lumot yetarli emas", "Текшириш учун маълумот етарли эмас"),
    ("Подтвердить находку", "Confirm finding", "Topilmani tasdiqlash", "Топилмани тасдиқлаш"),
    ("Отклонить находку", "Dismiss finding", "Topilmani rad etish", "Топилмани рад этиш"),
    ("Передать на проверку", "Refer for further review", "Qo‘shimcha tekshiruvga yuborish", "Қўшимча текширувга юбориш"),
    ("Текст оферты", "Offer text", "Oferta matni", "Оферта матни"),
    ("Нормативное приложение", "Regulatory appendix", "Normativ ilova", "Норматив илова"),
    ("Раздел не установлен", "Section not established", "Bo‘lim aniqlanmagan", "Бўлим аниқланмаган"),
    ("Локальная AI-модель + поиск по словам", "Local AI model + lexical search", "Lokal AI modeli + so‘zlar bo‘yicha qidiruv", "Локал AI модели + сўзлар бўйича қидирув"),
    ("Локальная AI-модель", "Local AI model", "Lokal AI modeli", "Локал AI модели"),
    ("Поиск по словам (без AI-модели)", "Lexical search (no AI model)", "So‘zlar bo‘yicha qidiruv (AI modelisiz)", "Сўзлар бўйича қидирув (AI моделисиз)"),
    ("сум", "UZS", "so‘m", "сўм"), ("рабочих дней", "working days", "ish kuni", "иш куни"), ("дней", "days", "kun", "кун"),
    ("Страховая сумма ОСАГО", "Total OSAGO insured amount", "OSAGO umumiy sug‘urta summasi", "ОСАГО умумий суғурта суммаси"),
    ("Срок выплаты после решения страховщика", "Payment deadline after the insurer's decision", "Sug‘urtalovchi qaroridan keyingi to‘lov muddati", "Суғурталовчи қароридан кейинги тўлов муддати"),
    ("Срок уведомления о решении", "Decision notification deadline", "Qaror haqida xabar berish muddati", "Қарор ҳақида хабар бериш муддати"),
    ("Явно указанная общая страховая сумма ОСАГО в сумах. Премия и отдельные лимиты не сравниваются.", "The explicit total OSAGO insured amount in UZS. Premiums and individual sublimits are excluded.", "So‘mda aniq ko‘rsatilgan OSAGO umumiy sug‘urta summasi. Sug‘urta mukofoti va alohida limitlar solishtirilmaydi.", "Сўмда аниқ кўрсатилган ОСАГО умумий суғурта суммаси. Суғурта мукофоти ва алоҳида лимитлар солиштирилмайди."),
    ("Срок выплаты страхового возмещения в рабочих днях после принятия решения страховщиком.", "The indemnity payment deadline in working days after the insurer adopts its decision.", "Sug‘urtalovchi qaror qabul qilganidan keyin sug‘urta tovonini to‘lash muddati, ish kunlarida.", "Суғурталовчи қарор қабул қилганидан кейин суғурта товонини тўлаш муддати, иш кунларида."),
    ("Срок уведомления страхователя о решении после письменного или электронного обращения за возмещением.", "The deadline to notify the policyholder of a decision after a written or electronic indemnity request.", "Yozma yoki elektron tovon so‘rovidan keyin sug‘urta qildiruvchiga qaror haqida xabar berish muddati.", "Ёзма ёки электрон товон сўровидан кейин суғурта қилдирувчига қарор ҳақида хабар бериш муддати."),
    ("Проверены только выбранные условия ОСАГО. Общая законность договора не оценивалась.", "Only the selected OSAGO conditions were checked. Overall contract legality was not assessed.", "Faqat tanlangan OSAGO shartlari tekshirildi. Shartnomaning umumiy qonuniyligi baholanmadi.", "Фақат танланган ОСАГО шартлари текширилди. Шартноманинг умумий қонунийлиги баҳоланмади."),
    ("Интерпретации ожидают проверки квалифицированным юристом: PENDING_LEGAL_REVIEW. Это не юридическое заключение.", "Interpretations await qualified legal review: PENDING_LEGAL_REVIEW. This is not a legal opinion.", "Talqinlar malakali yurist tekshiruvini kutmoqda: PENDING_LEGAL_REVIEW. Bu huquqiy xulosa emas.", "Талқинлар малакали юрист текширувини кутмоқда: PENDING_LEGAL_REVIEW. Бу ҳуқуқий хулоса эмас."),
    ("Отсутствие найденного текста не доказывает нарушение. Поиск, в том числе AI, может пропустить нужный пункт.", "Missing text does not prove a violation. Retrieval, including AI, may miss a relevant clause.", "Matn topilmagani qonun buzilganini isbotlamaydi. Qidiruv, jumladan AI, kerakli bandni o‘tkazib yuborishi mumkin.", "Матн топилмагани қонун бузилганини исботламайди. Қидирув, жумладан AI, керакли бандни ўтказиб юбориши мумкин."),
    ("OCR не поддерживается. Нечитаемые страницы, сложная верстка и поврежденный текст ограничивают выводы.", "OCR is unsupported. Unreadable pages, complex layouts and damaged text limit conclusions.", "OCR qo‘llab-quvvatlanmaydi. O‘qilmaydigan sahifalar, murakkab tuzilish va buzilgan matn xulosalarni cheklaydi.", "OCR қўллаб-қувватланмайди. Ўқилмайдиган саҳифалар, мураккаб тузилиш ва бузилган матн хулосаларни чеклайди."),
    ("Неизвестная дата или неподдерживаемая редакция нормы не позволяют сделать числовое сравнение.", "An unknown date or unsupported legal version prevents numerical comparison.", "Noma’lum sana yoki qo‘llab-quvvatlanmaydigan norma tahriri sonli solishtirishga yo‘l qo‘ymaydi.", "Номаълум сана ёки қўллаб-қувватланмайдиган норма таҳрири сонли солиштиришга йўл қўймайди."),
    ("Отнесение текста к оферте или нормативному приложению эвристическое; его следует проверить по PDF.", "Offer/appendix classification is heuristic and should be checked against the PDF.", "Matnni oferta yoki normativ ilovaga ajratish taxminiy; uni PDF hujjati bo‘yicha tekshirish kerak.", "Матнни оферта ёки норматив иловага ажратиш тахминий; уни PDF ҳужжати бўйича текшириш керак."),
    ("Проверено условий: {total}. Возможных несоответствий: {conflicts}; согласуются с критериями: {matches}; не найдены: {missing}; недостаточно данных: {unverifiable}.", "Conditions checked: {total}. Possible inconsistencies: {conflicts}; consistent with criteria: {matches}; not found: {missing}; insufficient information: {unverifiable}.", "Tekshirilgan shartlar: {total}. Ehtimoliy nomuvofiqliklar: {conflicts}; mezonlarga mos: {matches}; topilmadi: {missing}; ma’lumot yetarli emas: {unverifiable}.", "Текширилган шартлар: {total}. Эҳтимолий номувофиқликлар: {conflicts}; мезонларга мос: {matches}; топилмади: {missing}; маълумот етарли эмас: {unverifiable}."),
    ("Ни одно условие не удалось надежно проверить. Это не устанавливает нарушение закона.", "None of the conditions could be verified reliably. This does not establish a violation of law.", "Hech bir shartni ishonchli tekshirib bo‘lmadi. Bu qonun buzilganini tasdiqlamaydi.", "Ҳеч бир шартни ишончли текшириб бўлмади. Бу қонун бузилганини тасдиқламайди."),
    ("Специалисту следует проверить отмеченные положения и применимую редакцию нормы.", "A specialist should review the flagged clauses and applicable legal version.", "Mutaxassis belgilangan bandlar va qo‘llanadigan norma tahririni tekshirishi kerak.", "Мутахассис белгиланган бандлар ва қўлланадиган норма таҳририни текшириши керак."),
    ("Результат относится только к указанным проверкам и не подтверждает законность всего договора.", "Results cover only these checks and do not confirm the legality of the entire contract.", "Natija faqat ushbu tekshiruvlarga tegishli va butun shartnomaning qonuniyligini tasdiqlamaydi.", "Натижа фақат ушбу текширувларга тегишли ва бутун шартноманинг қонунийлигини тасдиқламайди."),
    ("Значение не установлено", "Value not established", "Qiymat aniqlanmagan", "Қиймат аниқланмаган"),
    ("В тексте извлечено: ", "Extracted from the text: ", "Matndan ajratilgan qiymat: ", "Матндан ажратилган қиймат: "),
    ("Эти значения недостаточны для надежного сравнения; см. причину.", "These values are insufficient for reliable comparison; see the reason.", "Bu qiymatlar ishonchli solishtirish uchun yetarli emas; sababini ko‘ring.", "Бу қийматлар ишончли солиштириш учун етарли эмас; сабабини кўринг."),
    ("Подходящее доказательство не найдено. Числовое значение не установлено.", "No qualifying evidence was located. No numerical value was established.", "Mos dalil topilmadi. Sonli qiymat aniqlanmagan.", "Мос далил топилмади. Сонли қиймат аниқланмаган."),
    ("Найден связанный текст, но сопоставимое числовое условие не установлено.", "Related text was found, but no comparable numerical condition was established.", "Tegishli matn topildi, ammo solishtiriladigan sonli shart aniqlanmadi.", "Тегишли матн топилди, аммо солиштириладиган сонли шарт аниқланмади."),
    ("Применимая версия нормы не установлена; ориентир не выбран.", "The applicable legal version is unknown; no reference value was selected.", "Qo‘llanadigan norma tahriri aniqlanmagan; mezon qiymati tanlanmagan.", "Қўлланадиган норма таҳрири аниқланмаган; мезон қиймати танланмаган."),
    ("Ориентир общей суммы: ", "Total insured amount reference: ", "Umumiy summa mezoni: ", "Умумий сумма мезони: "),
    ("Предельный срок для этой проверки: ", "Maximum deadline for this check: ", "Ushbu tekshiruv uchun eng ko‘p muddat: ", "Ушбу текширув учун энг кўп муддат: "),
    ("Установите дату применимости договора по первичным документам и повторите проверку.", "Confirm the contract applicability date from primary documents and rerun the review.", "Asl hujjatlardan shartnomaning qo‘llanish sanasini aniqlang va tekshiruvni takrorlang.", "Асл ҳужжатлардан шартноманинг қўлланиш санасини аниқланг ва текширувни такрорланг."),
    ("Проверьте даты и обратитесь к специалисту за редакцией нормы для этой даты.", "Check the dates and ask a specialist to identify the legal version for that date.", "Sanalarni tekshiring va shu sana uchun norma tahririni aniqlashda mutaxassisga murojaat qiling.", "Саналарни текширинг ва шу сана учун норма таҳририни аниқлашда мутахассисга мурожаат қилинг."),
    ("Проверьте, как правила приложения включены в договор. Текст закона не подтверждает обязательство автора оферты.", "Check how the appendix rules are incorporated into the contract. Statutory text does not establish the offer author's commitment.", "Ilova qoidalari shartnomaga qanday kiritilganini tekshiring. Qonun matni oferta muallifining majburiyatini tasdiqlamaydi.", "Илова қоидалари шартномага қандай киритилганини текширинг. Қонун матни оферта муаллифининг мажбуриятини тасдиқламайди."),
    ("Откройте указанные в договоре правила и передайте вопрос об их применимости на правовую проверку.", "Open the rules referenced in the contract and request legal review of their applicability.", "Shartnomada ko‘rsatilgan qoidalarni oching va ularning qo‘llanishi bo‘yicha huquqiy tekshiruv so‘rang.", "Шартномада кўрсатилган қоидаларни очинг ва уларнинг қўлланиши бўйича ҳуқуқий текширув сўранг."),
    ("Сверьте цитату, дату и контекст в оригинале. Совпадение этого условия не подтверждает весь договор.", "Check the quotation, date and context in the original. A match for this condition does not approve the entire contract.", "Iqtibos, sana va kontekstni asl hujjatda tekshiring. Bu shartning mosligi butun shartnomani tasdiqlamaydi.", "Иқтибос, сана ва контекстни асл ҳужжатда текширинг. Бу шартнинг мослиги бутун шартномани тасдиқламайди."),
    ("Сверьте значение, событие и дату в PDF; передайте положение специалисту для правовой проверки.", "Check the value, event and date in the PDF; refer the clause to a specialist for legal review.", "PDF hujjatida qiymat, hodisa va sanani tekshiring; bandni huquqiy tekshiruv uchun mutaxassisga yuboring.", "PDF ҳужжатида қиймат, ҳодиса ва санани текширинг; бандни ҳуқуқий текширув учун мутахассисга юборинг."),
    ("Проверьте оригинал и связанные документы вручную. Не считайте отсутствие находки нарушением.", "Check the original and related documents manually. Do not treat a missing finding as a violation.", "Asl va tegishli hujjatlarni qo‘lda tekshiring. Topilma yo‘qligini qonun buzilishi deb hisoblamang.", "Асл ва тегишли ҳужжатларни қўлда текширинг. Топилма йўқлигини қонун бузилиши деб ҳисобламанг."),
    ("Проверьте оригинальный текст, единицы, событие и конкурирующие условия; при необходимости запросите читаемый PDF.", "Check the original text, units, trigger event and competing clauses; request a readable PDF if necessary.", "Asl matn, birliklar, boshlanish hodisasi va qarama-qarshi shartlarni tekshiring; zarur bo‘lsa, o‘qiladigan PDF hujjatini so‘rang.", "Асл матн, бирликлар, бошланиш ҳодисаси ва қарама-қарши шартларни текширинг; зарур бўлса, ўқиладиган PDF ҳужжатини сўранг."),
    ("В документе указано {actual}, а ориентир выбранной редакции — {reference}. Числовое расхождение требует проверки специалистом.", "The document states {actual}, while the selected version's reference is {reference}. The numerical difference requires specialist review.", "Hujjatda {actual} ko‘rsatilgan, tanlangan tahrir mezoni esa {reference}. Sonli farq mutaxassis tekshiruvini talab qiladi.", "Ҳужжатда {actual} кўрсатилган, танланган таҳрир мезони эса {reference}. Сонли фарқ мутахассис текширувини талаб қилади."),
    ("Применимая редакция не установлена", "Applicable version not established", "Qo‘llanadigan tahrir aniqlanmagan", "Қўлланадиган таҳрир аниқланмаган"),
    ("С {start} по {end}", "From {start} through {end}", "{start} dan {end} gacha", "{start} дан {end} гача"),
    ("конец подтвержденного диапазона каталога", "the end of the verified catalogue range", "katalogning tasdiqlangan oralig‘i oxiri", "каталогнинг тасдиқланган оралиғи охири"),
    ("Дата применимости договора не подтверждена. Дата аудита не заменяет дату договора.", "The contract applicability date is unconfirmed. The audit date does not replace the contract date.", "Shartnomaning qo‘llanish sanasi tasdiqlanmagan. Tekshiruv sanasi shartnoma sanasi o‘rnini bosmaydi.", "Шартноманинг қўлланиш санаси тасдиқланмаган. Текширув санаси шартнома санаси ўрнини босмайди."),
    ("Дата вне подтвержденного диапазона версий либо позже даты аудита.", "The date is outside the verified version range or later than the audit date.", "Sana tahrirlarning tasdiqlangan oralig‘idan tashqarida yoki tekshiruv sanasidan keyin.", "Сана таҳрирларнинг тасдиқланган оралиғидан ташқарида ёки текширув санасидан кейин."),
    ("Текст найден только в предполагаемом нормативном приложении; условие автора оферты не подтверждено.", "Text was found only in a suspected regulatory appendix; the offer author's condition is not established.", "Matn faqat taxminiy normativ ilovada topildi; oferta muallifining sharti tasdiqlanmagan.", "Матн фақат тахминий норматив иловада топилди; оферта муаллифининг шарти тасдиқланмаган."),
    ("Есть ссылка на правила №141; включение условий по ссылке требует правовой проверки.", "The document references rules under Resolution 141; incorporation by reference requires legal review.", "141-son qaror qoidalariga havola mavjud; shartlarni havola orqali kiritish huquqiy tekshiruvni talab qiladi.", "141-сон қарор қоидаларига ҳавола мавжуд; шартларни ҳавола орқали киритиш ҳуқуқий текширувни талаб қилади."),
    ("Часть документа не читается. Отсутствие условия не установлено.", "Part of the document is unreadable. The absence of the condition is not established.", "Hujjatning bir qismi o‘qilmaydi. Shart yo‘qligi aniqlanmagan.", "Ҳужжатнинг бир қисми ўқилмайди. Шарт йўқлиги аниқланмаган."),
    ("В извлеченном тексте и выбранных поиском фрагментах условие не найдено. Это не доказательство нарушения.", "The condition was not found in extracted text and retrieved passages. This is not proof of a violation.", "Ajratilgan matn va qidiruv tanlagan parchalar ichida shart topilmadi. Bu qonun buzilganining isboti emas.", "Ажратилган матн ва қидирув танлаган парчалар ичида шарт топилмади. Бу қонун бузилганининг исботи эмас."),
    ("Найдены конкурирующие значения или неоднозначные условия; требуется проверка контекста.", "Competing values or ambiguous conditions were found; review the context.", "Qarama-qarshi qiymatlar yoki noaniq shartlar topildi; kontekstni tekshirish zarur.", "Қарама-қарши қийматлар ёки ноаниқ шартлар топилди; контекстни текшириш зарур."),
    ("Найдено явное условие, согласующееся с числовым ориентиром и проверяемым событием. Вывод касается только этого условия.", "An explicit condition matches the numerical reference and checked event. The conclusion covers only this condition.", "Sonli mezon va tekshirilgan hodisaga mos aniq shart topildi. Xulosa faqat shu shartga tegishli.", "Сонли мезон ва текширилган ҳодисага мос аниқ шарт топилди. Хулоса фақат шу шартга тегишли."),
    ("Условие, пример или отрицание требуют ручного толкования.", "A conditional clause, example or negation requires manual interpretation.", "Shartli band, misol yoki inkor qo‘lda talqin qilishni talab qiladi.", "Шартли банд, мисол ёки инкор қўлда талқин қилишни талаб қилади."),
    ("Не установлен контекст общей страховой суммы.", "The total insured amount context was not established.", "Umumiy sug‘urta summasi konteksti aniqlanmagan.", "Умумий суғурта суммаси контексти аниқланмаган."),
    ("Возможна премия или частичный лимит вместо общей суммы.", "The value may be a premium or sublimit rather than the total insured amount.", "Qiymat umumiy summa emas, sug‘urta mukofoti yoki qisman limit bo‘lishi mumkin.", "Қиймат умумий сумма эмас, суғурта мукофоти ёки қисман лимит бўлиши мумкин."),
    ("Сумма/валюта отсутствует либо содержит несколько значений.", "The amount/currency is missing or contains multiple values.", "Summa yoki valyuta yo‘q, yoxud bir nechta qiymat mavjud.", "Сумма ёки валюта йўқ, ёхуд бир нечта қиймат мавжуд."),
    ("Неоднозначный формат числа.", "The number format is ambiguous.", "Son formati noaniq.", "Сон формати ноаниқ."),
    ("Диапазон или неравенство суммы требует ручного толкования.", "An amount range or inequality requires manual interpretation.", "Summa oralig‘i yoki tengsizlik qo‘lda talqin qilishni talab qiladi.", "Сумма оралиғи ёки тенгсизлик қўлда талқин қилишни талаб қилади."),
    ("Не найден единственный поддерживаемый срок в днях.", "No single supported deadline in days was found.", "Kunlarda yagona qo‘llab-quvvatlanadigan muddat topilmadi.", "Кунларда ягона қўллаб-қувватланадиган муддат топилмади."),
    ("Не подтвержден отсчет от принятия решения страховщиком.", "The deadline's start at the insurer's decision was not confirmed.", "Muddat sug‘urtalovchi qaroridan boshlanishi tasdiqlanmagan.", "Муддат суғурталовчи қароридан бошланиши тасдиқланмаган."),
    ("Не подтверждены рабочие дни; календарные дни нельзя сравнить автоматически.", "Working days were not confirmed; calendar days cannot be compared automatically.", "Ish kunlari tasdiqlanmagan; kalendar kunlarini avtomatik solishtirib bo‘lmaydi.", "Иш кунлари тасдиқланмаган; календарь кунларини автоматик солиштириб бўлмайди."),
    ("Не подтверждены обращение и адресат уведомления.", "The request trigger and notification recipient were not confirmed.", "Murojaat hodisasi va xabarnoma oluvchisi tasdiqlanmagan.", "Мурожаат ҳодисаси ва хабарнома олувчиси тасдиқланмаган."),
    ("В норме не указаны рабочие дни; требуется правовое толкование.", "The reference does not specify working days; legal interpretation is required.", "Normada ish kunlari ko‘rsatilmagan; huquqiy talqin zarur.", "Нормада иш кунлари кўрсатилмаган; ҳуқуқий талқин зарур."),
    ("Предварительная проверка", "Preliminary review", "Dastlabki tekshiruv", "Дастлабки текширув"),
    ("Предварительная проверка страхового документа", "Preliminary Insurance Document Review", "Sug‘urta hujjatining dastlabki tekshiruvi", "Суғурта ҳужжатининг дастлабки текшируви"),
    ("Не юридическое заключение. Проверка отдельных условий помогает специалисту найти и оценить доказательства.", "Not a legal opinion. Reviewing individual conditions helps a specialist locate and assess evidence.", "Bu huquqiy xulosa emas. Alohida shartlarni tekshirish mutaxassisga dalillarni topish va baholashga yordam beradi.", "Бу ҳуқуқий хулоса эмас. Алоҳида шартларни текшириш мутахассисга далилларни топиш ва баҳолашга ёрдам беради."),
    ("Создан (UTC)", "Created (UTC)", "Yaratilgan (UTC)", "Яратилган (UTC)"),
    ("Продукт", "Product", "Mahsulot", "Маҳсулот"), ("Не подтверждена", "Not confirmed", "Tasdiqlanmagan", "Тасдиқланмаган"),
    ("Объем", "Scope", "Qamrov", "Қамров"),
    ("{checks} условия ОСАГО; {pages} страниц", "{checks} OSAGO conditions; {pages} pages", "{checks} ta OSAGO sharti; {pages} sahifa", "{checks} та ОСАГО шарти; {pages} саҳифа"),
    ("Идентификатор документа · SHA-256", "Document identifier · SHA-256", "Hujjat identifikatori · SHA-256", "Ҳужжат идентификатори · SHA-256"),
    ("Краткий итог", "Executive summary", "Qisqa xulosa", "Қисқа хулоса"),
    ("Все находки требуют ручной проверки контекста. Совпадение не означает одобрение договора.", "All findings require manual context review. A match does not approve the contract.", "Barcha topilmalar kontekstni qo‘lda tekshirishni talab qiladi. Moslik shartnomani tasdiqlash degani emas.", "Барча топилмалар контекстни қўлда текширишни талаб қилади. Мослик шартномани тасдиқлаш дегани эмас."),
    ("Обзор находок", "Findings overview", "Topilmalar sharhi", "Топилмалар шарҳи"),
    ("Результат", "Status", "Holat", "Ҳолат"), ("Наблюдение", "Key observation", "Asosiy kuzatuv", "Асосий кузатув"), ("Страница PDF", "Evidence page", "Dalil sahifasi", "Далил саҳифаси"),
    ("Ручная проверка", "Review required", "Tekshiruv zarur", "Текширув зарур"), ("Нет доказательства", "No evidence", "Dalil yo‘q", "Далил йўқ"), ("Да", "Yes", "Ha", "Ҳа"), ("Не запрошена", "Not requested", "So‘ralmagan", "Сўралмаган"),
    ("Подробные результаты", "Detailed findings", "Batafsil natijalar", "Батафсил натижалар"),
    ("Доказательства из документа", "Evidence from the document", "Hujjatdan olingan dalillar", "Ҳужжатдан олинган далиллар"),
    ("Официальный текст и редакция", "Official text and version", "Rasmiy matn va tahrir", "Расмий матн ва таҳрир"),
    ("Цитата применимой версии не выбрана. Не используйте текущий текст как основание для неизвестной даты.", "No applicable-version quotation was selected. Do not use current wording as authority for an unknown date.", "Qo‘llanadigan tahrir iqtibosi tanlanmagan. Noma’lum sana uchun joriy matnni asos sifatida ishlatmang.", "Қўлланадиган таҳрир иқтибоси танланмаган. Номаълум сана учун жорий матнни асос сифатида ишлатманг."),
    ("Неопределенность", "Uncertainty", "Noaniqlik", "Ноаниқлик"),
    ("Отдельные причины не зарегистрированы; правовая интерпретация все равно требует проверки.", "No separate uncertainty reason was recorded; legal interpretation still requires review.", "Alohida noaniqlik sababi qayd etilmagan; huquqiy talqin baribir tekshiruvni talab qiladi.", "Алоҳида ноаниқлик сабаби қайд этилмаган; ҳуқуқий талқин барибир текширувни талаб қилади."),
    ("Аннотация: {action} · {timestamp}", "Annotation: {action} · {timestamp}", "Izoh: {action} · {timestamp}", "Изоҳ: {action} · {timestamp}"),
    ("Ограничения и правовая проверка", "Limitations and legal review", "Cheklovlar va huquqiy tekshiruv", "Чекловлар ва ҳуқуқий текширув"),
    ("Ограничения этого анализа", "Limitations of this analysis", "Ushbu tahlil cheklovlari", "Ушбу таҳлил чекловлари"),
    ("Записи аналитика", "Analyst review record", "Tahlilchi yozuvlari", "Таҳлилчи ёзувлари"),
    ("Аннотации локального аналитика не являются правовой сертификацией. Исходные результаты сохранены. Записи живут в сессии, пока не экспортированы.", "Local analyst annotations are not legal certification. Original results are preserved. Records remain in the session unless exported.", "Lokal tahlilchi izohlari huquqiy sertifikat emas. Asl natijalar saqlanadi. Yozuvlar eksport qilinmaguncha sessiyada qoladi.", "Локал таҳлилчи изоҳлари ҳуқуқий сертификат эмас. Асл натижалар сақланади. Ёзувлар экспорт қилинмагунча сессияда қолади."),
    ("Аннотации отсутствуют.", "No annotations recorded.", "Izohlar qayd etilmagan.", "Изоҳлар қайд этилмаган."),
    ("Техническое приложение", "Technical appendix", "Texnik ilova", "Техник илова"),
    ("Схема / приложение", "Schema / application", "Sxema / ilova", "Схема / илова"), ("SHA-256 документа", "Document SHA-256", "Hujjat SHA-256 qiymati", "Ҳужжат SHA-256 қиймати"),
    ("Версия каталога", "Catalogue version", "Katalog tahriri", "Каталог таҳрири"), ("SHA-256 каталога", "Catalogue SHA-256", "Katalog SHA-256 qiymati", "Каталог SHA-256 қиймати"),
    ("Основание даты", "Date basis", "Sana asosi", "Сана асоси"), ("Запрошенный поиск", "Requested retrieval", "So‘ralgan qidiruv", "Сўралган қидирув"), ("Фактический поиск", "Actual retrieval", "Haqiqiy qidiruv", "Ҳақиқий қидирув"),
    ("Отбор фрагментов", "Candidate selection", "Parchalarni tanlash", "Парчаларни танлаш"), ("Ревизия модели", "Model revision", "Model tahriri", "Модель таҳрири"),
    ("Не подтверждена / модель не использовалась", "Unconfirmed / model not used", "Tasdiqlanmagan / model ishlatilmagan", "Тасдиқланмаган / модель ишлатилмаган"),
    ("Языки / письменности", "Languages / scripts", "Tillar / yozuvlar", "Тиллар / ёзувлар"),
    ("Время обработки, секунд", "Processing timings, seconds", "Qayta ishlash vaqti, soniya", "Қайта ишлаш вақти, сония"), ("Идентификаторы доказательств", "Evidence identifiers", "Dalil identifikatorlari", "Далил идентификаторлари"),
    ("смещение", "offset", "siljish", "силжиш"), ("значение", "value", "qiymat", "қиймат"),
    ("Координаты — объединение блоков текста, не точная геометрия цитаты. Визуальное выделение не выполнялось.", "Coordinates combine text blocks and are not exact quotation geometry. No visual highlighting was applied.", "Koordinatalar matn bloklari birikmasi, iqtibosning aniq joylashuvi emas. Vizual ajratish bajarilmagan.", "Координаталар матн блоклари бирикмаси, иқтибоснинг аниқ жойлашуви эмас. Визуал ажратиш бажарилмаган."),
    ("Предупреждения", "Warnings", "Ogohlantirishlar", "Огоҳлантиришлар"),
    ("PolisDiff AI · Печать → Сохранить как PDF. Оригинальные цитаты не переводились.", "PolisDiff AI · Print → Save as PDF. Original quotations remain untranslated.", "PolisDiff AI · Chop etish → PDF sifatida saqlash. Asl iqtiboslar tarjima qilinmagan.", "PolisDiff AI · Чоп этиш → PDF сифатида сақлаш. Асл иқтибослар таржима қилинмаган."),
    ("Ссылка не открывается: официальный HTTPS-источник не подтвержден.", "Link unavailable: the official HTTPS source is unconfirmed.", "Havola ochilmaydi: rasmiy HTTPS manbasi tasdiqlanmagan.", "Ҳавола очилмайди: расмий HTTPS манбаси тасдиқланмаган."),
    ("Оригинальное описание из каталога (без перевода)", "Recorded catalogue interpretation (original wording)", "Katalogdagi asl talqin (tarjimasiz)", "Каталогдаги асл талқин (таржимасиз)"),
    ("Официальные цитаты и сведения о редакции сохранены на языке источника; перевод интерфейса не является правовым толкованием.", "Official quotations and version notes remain in their source language; interface translations are not legal interpretations.", "Rasmiy iqtiboslar va tahrir ma’lumotlari manba tilida saqlanadi; interfeys tarjimasi huquqiy talqin emas.", "Расмий иқтибослар ва таҳрир маълумотлари манба тилида сақланади; интерфейс таржимаси ҳуқуқий талқин эмас."),
    ("Исходное пояснение: {text}", "Original recorded explanation: {text}", "Asl qayd etilgan izoh: {text}", "Асл қайд этилган изоҳ: {text}"),
    ("Страница {page}: текст недостаточен или поврежден; OCR отключен. Нужна ручная проверка.", "Page {page}: insufficient or damaged text; OCR is disabled. Manual review required.", "{page}-sahifa: matn yetarli emas yoki buzilgan; OCR o‘chirilgan. Qo‘lda tekshirish zarur.", "{page}-саҳифа: матн етарли эмас ёки бузилган; OCR ўчирилган. Қўлда текшириш зарур."),
    ("AI-поиск недоступен ({error}); использован поиск по словам.", "AI retrieval unavailable ({error}); lexical fallback used.", "AI qidiruvi mavjud emas ({error}); so‘zlar bo‘yicha qidiruv ishlatildi.", "AI қидируви мавжуд эмас ({error}); сўзлар бўйича қидирув ишлатилди."),
    ("OSAGO (выбрано пользователем)", "OSAGO (user selected)", "OSAGO (foydalanuvchi tanlagan)", "ОСАГО (фойдаланувчи танлаган)"),
]

from .finding_copy import ROWS as FINDING_ROWS
ROWS += FINDING_ROWS

TRANSLATIONS = {code: {} for code in LANGUAGES}
for row in ROWS:
    for code, value in zip(("ru", "en", "uz-Latn", "uz-Cyrl"), row):
        if row[0] in TRANSLATIONS[code]:
            raise ValueError(f"Duplicate translation: {row[0]}")
        TRANSLATIONS[code][row[0]] = value


def tr(key, language="ru", **values):
    """Strict fixed copy lookup; unsupported languages/keys are programming errors."""
    return TRANSLATIONS[language][key].format(**values)


def recorded_text(text, language="ru"):
    """Translate known engine reasons; explicitly retain unknown/custom original wording."""
    if text in TRANSLATIONS[language]:
        return tr(text, language)
    return text if language == "ru" else tr("Исходное пояснение: {text}", language, text=text)


def warning_text(text, language="ru"):
    if text == "All engineering interpretations are PENDING_LEGAL_REVIEW.":
        return tr("Интерпретации ожидают проверки квалифицированным юристом: PENDING_LEGAL_REVIEW. Это не юридическое заключение.", language)
    if text == "Offer/appendix classification is heuristic and requires manual review.":
        return tr("Отнесение текста к оферте или нормативному приложению эвристическое; его следует проверить по PDF.", language)
    match = re.fullmatch(r"Page (\d+): insufficient or damaged text; OCR is not enabled\. Manual review required\.", text)
    if match:
        return tr("Страница {page}: текст недостаточен или поврежден; OCR отключен. Нужна ручная проверка.", language, page=match[1])
    match = re.fullmatch(r"Semantic retrieval unavailable \((\w+)\); lexical fallback used\.", text)
    if match:
        return tr("AI-поиск недоступен ({error}); использован поиск по словам.", language, error=match[1])
    return recorded_text(text, language)


def placeholders(text):
    return {name for _, name, _, _ in Formatter().parse(text) if name is not None}


UNCERTAINTY_TEXT = {
    "applicable_date_unknown": "Дата применимости договора не подтверждена. Дата аудита не заменяет дату договора.",
    "unsupported_applicability_date": "Дата вне подтвержденного диапазона версий либо позже даты аудита.",
    "appendix_only": "Текст найден только в предполагаемом нормативном приложении; условие автора оферты не подтверждено.",
    "incorporation_by_reference": "Есть ссылка на правила №141; включение условий по ссылке требует правовой проверки.",
    "unreadable_pages": "Часть документа не читается. Отсутствие условия не установлено.",
    "retrieval_may_miss_evidence": "Отсутствие найденного текста не доказывает нарушение. Поиск, в том числе AI, может пропустить нужный пункт.",
    "competing_or_ambiguous_terms": "Найдены конкурирующие значения или неоднозначные условия; требуется проверка контекста.",
}


def uncertainty_text(text, language="ru"):
    return recorded_text(UNCERTAINTY_TEXT.get(text, text), language)


def disclaimer_text(text, language="ru"):
    from .models import Report
    if text == Report.model_fields['disclaimer'].default:
        return ' '.join(tr(value, language) for value in [
            "Проверены только выбранные условия ОСАГО. Общая законность договора не оценивалась.",
            "Отсутствие найденного текста не доказывает нарушение. Поиск, в том числе AI, может пропустить нужный пункт.",
            "Интерпретации ожидают проверки квалифицированным юристом: PENDING_LEGAL_REVIEW. Это не юридическое заключение."])
    return recorded_text(text, language)
