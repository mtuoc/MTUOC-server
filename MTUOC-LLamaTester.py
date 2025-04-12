import tkinter as tk
from tkinter import scrolledtext
import torch
from transformers import pipeline
import os

def translate_text():
    # Obtener el contenido de las entradas
    model_id = model_entry.get("1.0", tk.END).strip()
    role = role_entry.get("1.0", tk.END).strip()
    instruction = instruction_entry.get("1.0", tk.END).strip()

    if not model_id:
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, "Error: No model ID provided.")
        return

    try:
        # Configuración del modelo
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
    except Exception as e:
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, f"Error: {str(e)}")

def clear_instruction():
    instruction_entry.delete("1.0", tk.END)

def clear_output():
    output_text.delete("1.0", tk.END)

def copy_output():
    root.clipboard_clear()
    root.clipboard_append(output_text.get("1.0", tk.END).strip())
    root.update()  # Mantener el portapapeles actualizado

# Configurar la ventana principal
root = tk.Tk()
root.title("MTUOC LLM Tester")

# Crear una cuadrícula para la disposición
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)

# Entrada para el modelo
tk.Label(root, text="Model ID:").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))
model_entry = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=120, height=2)
model_entry.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")

# Entrada para "role"
tk.Label(root, text="Role:").grid(row=2, column=0, sticky="w", padx=10, pady=(10, 0))
role_entry = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=120, height=4)
role_entry.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")

# Entrada para la instrucción
tk.Label(root, text="Instruction:").grid(row=4, column=0, sticky="w", padx=10, pady=(10, 0))
instruction_entry = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=120, height=15)
instruction_entry.grid(row=5, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")

# Botón para limpiar instrucciones
clear_instruction_button = tk.Button(root, text="Clear Instruction", command=clear_instruction)
clear_instruction_button.grid(row=6, column=0, pady=(0, 10), sticky="ew", padx=10)

# Botón para ejecutar la traducción
translate_button = tk.Button(root, text="Generate", command=translate_text)
translate_button.grid(row=6, column=1, pady=(0, 10), sticky="ew", padx=10)

# Salida para mostrar el resultado
tk.Label(root, text="Output:").grid(row=7, column=0, sticky="w", padx=10, pady=(10, 0))
output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=120, height=20)
output_text.grid(row=8, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")

# Botones debajo del Output
output_buttons_frame = tk.Frame(root)
output_buttons_frame.grid(row=9, column=0, columnspan=2, pady=(0, 10), sticky="ew", padx=10)
clear_output_button = tk.Button(output_buttons_frame, text="Clear Output", command=clear_output)
clear_output_button.pack(side=tk.LEFT, padx=5)
copy_output_button = tk.Button(output_buttons_frame, text="Copy Output", command=copy_output)
copy_output_button.pack(side=tk.LEFT, padx=5)

# Ejecutar la aplicación
tk.mainloop()
