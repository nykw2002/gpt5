import os

def extract_final_answer(full_answer, query_classification):
    if query_classification.get('primary_type') == 'counting':
        lines = full_answer.split('\n')

        final_answer_start = -1
        for i, line in enumerate(lines):
            if 'FINAL ANSWER' in line.upper():
                final_answer_start = i
                break

        if final_answer_start != -1:
            final_lines = []
            capturing = False

            for line in lines[final_answer_start:]:
                if 'FINAL ANSWER' in line.upper():
                    capturing = True
                    continue
                elif capturing:
                    line = line.strip()
                    if line:
                        final_lines.append(line)

            if final_lines:
                return '\n'.join(final_lines)

    return full_answer

def get_file_size(file_path):
    try:
        return os.path.getsize(file_path)
    except:
        return 0