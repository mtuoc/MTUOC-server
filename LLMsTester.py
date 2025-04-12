import tkinter as tk
from tkinter import scrolledtext
import torch
from transformers import pipeline

def translate_text():
    # Obtener el contenido de las entradas
    role = role_entry.get("1.0", tk.END).strip()
    instruction = instruction_entry.get("1.0", tk.END).strip()

    # Configuración del modelo
    model_id = "meta-llama/Llama-3.2-3B-Instruct"
    pipe = pipeline(
        "text-generation",
        model=model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    # Formatear los mensajes
    messages = [
        {"role": "system", "content": role},
        {"role": "user", "content": instruction},
    ]

    # Generar la traducción
    outputs = pipe(messages, max_new_tokens=256)
    result = outputs[0]["generated_text"][-1]['content']

    # Mostrar el resultado en la salida
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, result)

# Configurar la ventana principal
root = tk.Tk()
root.title("LLaMA Translation GUI")

# Entrada para "role"
tk.Label(root, text="Role:").pack(anchor="w", padx=10, pady=(10, 0))
role_entry = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=4)
role_entry.pack(padx=10, pady=(0, 10), fill=tk.X)

# Entrada para la instrucción
tk.Label(root, text="Instruction:").pack(anchor="w", padx=10, pady=(10, 0))
instruction_entry = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20)
instruction_entry.pack(padx=10, pady=(0, 10), fill=tk.X)

# Botón para ejecutar la traducción
translate_button = tk.Button(root, text="Translate", command=translate_text)
translate_button.pack(pady=(0, 10))

# Salida para mostrar el resultado
tk.Label(root, text="Output:").pack(anchor="w", padx=10, pady=(10, 0))
output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20)
output_text.pack(padx=10, pady=(0, 10), fill=tk.X)

# Ejecutar la aplicación
tk.mainloop()
