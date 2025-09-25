import time

import librosa
import whisperx

device = "cuda"  # 如果没有GPU可以用 "cpu"
audio_file = "1.mp3"
output_srt = "output.srt"

# 参考文本
reference_text = (
    "接下来讲 轮廓算数平均偏差 这个问题。11221331122"
    "本节课将深入探讨工业机器人编程中的 程序跳转和标签相关内容。"
    "我们要 学习如何根据变量的正负情况来控制程序的执行路径， 具体来说就是如果两个变量正负符号相同，执行画圆和画三角的操作； 若符号相反则只执行画三角操作。 这其中涉及到一系列的操作步骤，我们将逐步学习编写这样的跳转函数程序。"
    "本节课开始编写跳转程序。 跳转程序在工业机器人编程里是非常关键的部分，它能够让程序根据不同的条件执行不同的任务。 就像在一个复杂的生产流程中，机器人需要根据不同的传感器信号或者数据状态来决定下一步的动作，跳转程序就能实现这样的智能决策。 这一页虽然没有详细的操作步骤，但我们要明确编写跳转程序是这部分内容的核心任务。"
    "​这里引入了我们的任务， 也就是编写一个程序对两个变量进行比较。 ​这个比较的结果将决定程序的执行路径。 在实际的工业场景中，例如在自动化装配线上，可能会有不同类型的零件需要处理，我们可以通过变量来表示零件的某些特征，如尺寸、重量等。 ​根据这些变量的正负情况，机器人执行不同的操作，像这里的画圆和画三角操作，这是一种很实用的编程逻辑。 ​掌握编写跳转函数程序的方法是这一任务的要求，这需要我们对程序的逻辑结构和指令有深入的理解。123"
    "首先，我们要在新建的例行程序“tiaozhuan”中，选择“IF”条件判断指令。这个“IF”指令就像是一个岔路口的指示牌，根据后面设定的条件决定程序是向左走还是向右走。在工业机器人编程中，“IF”指令是构建逻辑判断的基础，它可以根据各种条件，如传感器的反馈值、计数器的值等，来决定程序的流程。例如，机器人在搬运货物时，如果货物的重量超过某个设定值（这可以通过一个变量来表示），就执行特殊的搬运动作，这就可以用“IF”指令来实现。"
    "接下来点击“EXP”。这个操作可能是 为了扩展或者进入某个表达式编辑的界面。在编程中，表达式是构建逻辑和计算的重要部分。 例如，我们可能会在表达式中编写关于变量的计算式，像𝑝𝑙𝑢𝑠−𝑚𝑖𝑛𝑢𝑠，这个表达式的结果会影响后续的程序流程。它可能用于判断两个变量的大小关系或者其他逻辑关系，是实现跳转程序逻辑的关键环节。"
    "然后点击“更改数据类型…”按钮，选择“num”确定后，新建两个变量“plus”和“minus”。在编程里，数据类型的选择非常重要。“num”类型表示数字类型，这两个变量将用于我们的比较操作。在实际应用中，这两个变量可以代表很多实际意义的数值，比如机器人的运动速度、位置坐标等。通过对这些变量的比较，我们可以根据不同的情况调整机器人的动作。"
    "完成图示表达式的编写，并点击“确定”按钮。这个表达式的编写是根据我们的任务需求来的，可能是关于“plus”和“minus”这两个变量的某种运算或者比较关系。例如，可能是𝑝𝑙𝑢𝑠>𝑚𝑖𝑛𝑢𝑠这样的比较表达式，或者是𝑝𝑙𝑢𝑠+𝑚𝑖𝑛𝑢𝑠=10这样的计算表达式。这个表达式的结果将作为“IF”条件判断的依据，从而决定程序的跳转方向。"
    "点击“GOTO”指令。“GOTO”指令是实现程序跳转的关键指令。它可以让程序直接跳转到指定的位置。在大型的工业机器人程序中，当满足某些特定条件时，我们可以使用“GOTO”指令快速跳转到需要执行特定任务的代码段。比如，当机器人检测到某个故障信号时，使用“GOTO”指令跳转到故障处理的程序段。"
    "选中“IF…”整个语句段，点击进人图示界面，点击“添加ELSEIF”按钮。“ELSEIF”语句是对“IF”语句的补充，它可以增加更多的条件判断分支。在实际的编程中，可能会有多种情况需要考虑，不仅仅是简单的“是”或者“否”的判断。例如，除了判断两个变量的正负关系，还可能需要判断变量是否等于某个特定值等情况，这时“ELSEIF”就非常有用了。"
    "添加了一个“ELSEIF”语句，点击“确定”按钮。这个操作完善了我们的条件判断结构。通过添加“ELSEIF”语句，我们的程序可以处理更多复杂的情况。例如，在机器人的路径规划中，如果第一种条件下的路径被占用，我们可以通过“ELSEIF”语句来判断其他可能的路径情况。"
    "然后参考本任务操作的步骤1～6，完成如图所示指令的编写。这一步是对前面操作的巩固和延续。按照之前的步骤，我们可以构建出更复杂、更符合实际需求的程序逻辑。在这个过程中，要注意每个指令的参数设置和逻辑关系的准确性，确保程序能够按照预期的方式运行。"
    "选中“IF…”语句段，点击图示中的“Label”指令完成添加。“Label”标签在程序中起到标记特定位置的作用，就像地图上的地标一样。在跳转程序中，我们可以通过标签来指定跳转的目标位置，这样可以使程序的结构更加清晰，逻辑更加易于理解。"
    "点击“ID”。这一步是为了给标签设置一个唯一的标识符，以便在程序中准确地引用这个标签。在一个复杂的程序中，可能会有多个标签，每个标签都需要有一个独特的“ID”来区分，避免程序在跳转时出现混乱。"
    "将“ID”名编写成“A”，完成标签A的添加。 这个标签“A”就是我们程序中的一个重要标记点。 在后续的程序中，当满足某些条件时，程序就可以跳转到这个标签所标记的位置。例如，当两个变量正负相同，我们可以让程序跳转到标签“A”处执行画圆和画三角的操作。"
    "添加“ProCall”指令，调用圆形轨迹的例行程序。“ProCall”指令用于调用其他已经编写好的例行程序。在工业机器人编程中，我们可以将一些常用的操作编写成独立的例行程序，然后在需要的时候通过“ProCall”指令来调用。这样可以提高代码的复用性，减少代码的冗余。"
    "参考本任务操作的步骤9～12，完成如图所示程序的缩写。这一步是对前面操作的再次巩固和优化。通过按照一定的步骤进行操作，我们可以构建出更加简洁、高效的程序结构，使程序在运行时能够更加稳定、准确地执行任务。"
    "要实现同号执行画圆和三角的程序，异号执行画三角形，即IF条件大于0时，跳转到标签A，将圆和三角形程序依次执行。这里明确了程序的执行逻辑。当我们比较的两个变量的结果满足大于0这个条件时，就会跳转到标签A处。这就像在自动化生产线上，根据产品的不同类型（可以用变量表示），机器人执行不同的加工操作。如果产品类型满足某种条件（这里就是变量比较结果大于0），就执行一系列特定的加工步骤（画圆和画三角）。"
    "IF条件小于0时，跳转到标签B，只执行“sanjiaoxing”程序，即只画三角形。这是另一种情况的处理。当变量比较结果小于0时，程序跳转到标签B执行画三角形操作。这体现了程序的灵活性，可以根据不同的条件执行不同的任务，适应各种实际的工业生产需求。"
    "标签号设置完成好后，即完成了程序的编写，如图所示。到这一步，我们已经按照要求完成了整个跳转程序的编写。这个程序可以根据变量的正负情况，准确地控制机器人执行不同的图形绘制操作，在实际的工业机器人编程中，这种根据不同条件执行不同任务的编程方式非常常见，可以用于各种复杂的生产流程控制。"
    "本节课我们主要学习了工业机器人编程中的程序跳转和标签相关知识。从最开始在例行程序中选择“IF”条件判断指令，到新建变量、编写表达式、添加“ELSEIF”语句，再到设置标签和编写跳转逻辑等一系列操作。我们通过对两个变量正负情况的判断，实现了不同的程序执行路径，即同号时执行画圆和画三角，异号时只执行画三角。"
    "这些操作步骤和编程逻辑在工业机器人的实际应用中非常重要，可以让机器人根据不同的工作场景和任务需求，灵活地调整工作流程。"
)


def get_audio_duration(audio_file):
    """获取音频文件的准确时长（秒）"""
    duration = librosa.get_duration(path=audio_file)
    return duration


# 获取音频准确时长
audio_duration = get_audio_duration(audio_file)
print(f"音频文件时长: {audio_duration:.2f}秒")

# 加载音频
audio = whisperx.load_audio(audio_file)

# 创建包含参考文本的segments（使用准确的音频时长）
transcript_segments = [{"text": reference_text, "start": 0, "end": audio_duration}]

# 加载对齐模型并进行强制对齐
print("\n正在加载对齐模型...")
model_a, metadata = whisperx.load_align_model(language_code="zh", device=device)

print("正在进行强制对齐...")
# 记录对齐时间
start_time = time.time()
aligned_result = whisperx.align(
    transcript_segments, model_a, metadata, audio, device
)
end_time = time.time()
print(f"对齐时间: {end_time - start_time:.2f}秒")


# 处理对齐结果并按标点分割生成SRT文件
def split_by_punctuation(text):
    """按标点符号分割文本"""

    # 中文标点符号
    punctuation_marks = ['。', '！', '？', '；', '，', '、', '.', '!', '?', ';', ',']

    # 找到所有标点符号的位置
    sentences = []
    current_sentence = ""
    sentence_start_char = 0

    for i, char in enumerate(text):
        current_sentence += char
        if char in punctuation_marks or i == len(text) - 1:
            # 找到句子结束，记录句子和字符位置
            sentences.append({
                'text': current_sentence.strip(),
                'start_char': sentence_start_char,
                'end_char': i + 1
            })
            current_sentence = ""
            sentence_start_char = i + 1

    return sentences


def assign_timestamps_to_sentences(sentences, word_segments, full_text):
    """为句子分配时间戳"""
    result_segments = []

    # 创建字符位置到词段的映射
    char_to_word = {}
    text_pos = 0

    for word_seg in word_segments:
        word_text = word_seg['word']
        # 为这个词的每个字符分配词段信息
        for i in range(len(word_text)):
            if text_pos + i < len(full_text):
                char_to_word[text_pos + i] = word_seg
        text_pos += len(word_text)

    for sentence in sentences:
        if not sentence['text']:
            continue

        sentence_start = sentence['start_char']
        sentence_end = sentence['end_char']

        # 找到句子范围内的所有词段
        sentence_words = []
        seen_words = set()

        for char_pos in range(sentence_start, min(sentence_end, len(full_text))):
            if char_pos in char_to_word:
                word_seg = char_to_word[char_pos]
                word_id = id(word_seg)  # 使用对象ID避免重复
                if word_id not in seen_words:
                    sentence_words.append(word_seg)
                    seen_words.add(word_id)

        if sentence_words:
            # 按时间戳排序确保正确的开始和结束时间
            sentence_words.sort(key=lambda x: x['start'])
            start_time = sentence_words[0]['start']
            end_time = sentence_words[-1]['end']

            result_segments.append({
                'text': sentence['text'],
                'start': start_time,
                'end': end_time
            })

    return result_segments


def format_time_srt(seconds):
    """将秒数转换为SRT时间格式 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"


def generate_srt(segments, output_file):
    """生成SRT字幕文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, 1):
            start_time = format_time_srt(segment['start'])
            end_time = format_time_srt(segment['end'])
            text = segment['text']

            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")


# 检查对齐结果
if 'segments' in aligned_result and aligned_result['segments']:
    print("\n对齐成功！开始处理字幕...")

    # 获取所有词段
    all_words = []
    full_text = ""

    for segment in aligned_result['segments']:
        if 'words' in segment:
            for word in segment['words']:
                if 'start' in word and 'end' in word:
                    all_words.append(word)
                    full_text += word['word']

    print(f"识别到 {len(all_words)} 个词段")
    print(f"完整文本长度: {len(full_text)} 字符")

    # 按标点分割句子
    sentences = split_by_punctuation(full_text)
    print(f"按标点分割为 {len(sentences)} 个句子")

    # 为句子分配时间戳
    timed_segments = assign_timestamps_to_sentences(sentences, all_words, full_text)
    print(f"成功分配时间戳的句子: {len(timed_segments)} 个")

    # 生成SRT文件
    generate_srt(timed_segments, output_srt)
    print(f"\nSRT文件已生成: {output_srt}")

    # 显示前几个字幕段落作为预览
    print("\n字幕预览:")
    for i, segment in enumerate(timed_segments[:5]):
        start_time = format_time_srt(segment['start'])
        end_time = format_time_srt(segment['end'])
        print(f"{i + 1}. [{start_time} --> {end_time}] {segment['text']}")

    if len(timed_segments) > 5:
        print(f"... 还有 {len(timed_segments) - 5} 个字幕段落")

else:
    print("对齐失败，没有找到有效的词段信息")
