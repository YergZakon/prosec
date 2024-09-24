import streamlit as st
import anthropic
from io import StringIO
import json
import time

# Функция для создания эффекта печати
def typewriter(text, speed=0.03):
    container = st.empty()
    displayed_text = ""
    for char in text:
        displayed_text += char
        container.markdown(displayed_text)
        time.sleep(speed)
    return container

# Функция для загрузки примеров речей
@st.cache_data
def load_speech_examples():
    try:
        with open('speech_examples.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        st.error("Файл с примерами речей не найден. Пожалуйста, убедитесь, что файл 'speech_examples.json' находится в той же директории, что и приложение.")
        return []
    except json.JSONDecodeError:
        st.error("Ошибка при чтении файла с примерами речей. Проверьте формат JSON.")
        return []

# Инициализация клиента Claude
@st.cache_resource
def init_claude_client():
    return anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

def extract_and_analyze_act(client, text):
    prompt = f"""
    Проанализируйте следующий обвинительный акт и извлеките из него ключевую информацию:

    {text}

    Пожалуйста, предоставьте следующую информацию в формате JSON:
    1. ФИО подозреваемого
    2. Дата преступления
    3. Статья обвинения
    4. Информация о предыдущих судимостях
    5. Краткое описание обстоятельств дела
    6. Любые смягчающие обстоятельства
    7. Любые отягчающие обстоятельства
    8. Сумма ущерба (если применимо)
    """

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1500,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return json.loads(response.content[0].text), response.usage.output_tokens

def generate_speech_claude(client, data, examples):
    examples_text = "\n\n".join([example["content"] for example in examples])
    prompt = f"""
    На основе следующей информации, извлеченной из обвинительного акта, сгенерируйте обвинительную речь прокурора:

    {json.dumps(data, ensure_ascii=False, indent=2)}

    Используйте следующие примеры обвинительных речей как образец стиля, структуры и уровня детализации:

    {examples_text}

    Ваша речь должна точно следовать структуре и стилю примеров, включая:
    1. Вступительное слово с указанием ФИО подсудимого, статьи обвинения и даты преступления
    2. Подробное изложение фактов дела с указанием конкретных дат, сумм и обстоятельств
    3. Анализ доказательств с перечислением конкретных доказательств вины
    4. Четкую юридическую квалификацию деяния
    5. Обоснование предлагаемого наказания с учетом смягчающих и отягчающих обстоятельств
    6. Заключительную часть с конкретным запросом о сроке и виде наказания, а также о возмещении ущерба

    Обязательно укажите конкретный запрашиваемый срок наказания в годах и месяцах, основываясь на санкции соответствующей статьи УК РК и обстоятельствах дела.

    Используйте формальный юридический язык и структуру, характерную для обвинительной речи в суде Казахстана.
    """

    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.content[0].text, response.usage.output_tokens

st.title("Генератор обвинительной речи на основе обвинительного акта")

claude_client = init_claude_client()
speech_examples = load_speech_examples()

if not speech_examples:
    st.warning("Примеры речей не загружены. Генерация речи может быть менее точной.")

uploaded_file = st.file_uploader("Загрузите обвинительный акт", type="txt")

if uploaded_file is not None:
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    act_text = stringio.read()
    
    with st.spinner('Анализ обвинительного акта...'):
        extracted_info, analysis_tokens = extract_and_analyze_act(claude_client, act_text)
    
    st.subheader("Извлеченная информация")
    st.json(extracted_info)
    st.info(f"Токены, использованные для анализа: {analysis_tokens}")
    
    if st.button("Сгенерировать речь"):
        with st.spinner('Генерация речи...'):
            speech, speech_tokens = generate_speech_claude(claude_client, extracted_info, speech_examples)
        
        st.subheader("Сгенерированная обвинительная речь")
        speech_container = typewriter(speech)
        
        # Добавляем кнопку для копирования текста
        if st.button("Копировать речь"):
            st.code(speech)  # Отображаем текст в формате, удобном для копирования
        
        st.info(f"Токены, использованные для генерации речи: {speech_tokens}")

        total_tokens = analysis_tokens + speech_tokens
        st.success(f"Общее количество использованных токенов: {total_tokens}")

st.markdown("""
    ### Инструкция по использованию:
    1. Загрузите файл обвинительного акта в формате .txt
    2. После загрузки будет проведен анализ и извлечение ключевой информации
    3. Проверьте извлеченную информацию
    4. Нажмите кнопку "Сгенерировать речь" для создания обвинительной речи
    5. Наблюдайте, как речь "печатается" на экране
    6. При необходимости используйте кнопку "Копировать речь" для копирования всего текста
    7. Ознакомьтесь с информацией об использованных токенах
""")
