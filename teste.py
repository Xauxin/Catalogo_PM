from name_maker import MotorBordado

teste = MotorBordado("Monotype_Corsiva")
text = "Dalton"
bordado = teste.gerar_nome(text, 400)
bordadomenor = teste.gerar_nome(text, 370)
bordado.write("teste.dst")
bordadomenor.write("teste_menor.dst")