import json
import os
from pathlib import Path

import freetype
from pyembroidery import COLOR_CHANGE, END, NO_COMMAND, EmbPattern


class MotorBordado:
    def __init__(self, font_name):
        self.font_name = font_name
        self.font_path = Path("./fontsfiles") / font_name
        self.tentativa = 0
        config = self._carregar_config_fonte()

        if "tamanhos_disponiveis" not in config:
            raise ValueError(
                f"Configuração 'tamanhos_disponiveis' ausente para a fonte: {font_name}"
            )
        self.tamanhos_disponiveis = config["tamanhos_disponiveis"]

    def _configurar_escala(self, pasta_tamanho_dst):
        dst_folder = os.path.join(pasta_tamanho_dst)

        ttf_path = os.path.join(self.font_path, f"{self.font_name}.ttf")
        if not os.path.exists(ttf_path):
            raise FileNotFoundError(
                f"Config Escala: Arquivo TTF não encontrado: {ttf_path}"
            )

        self.face = freetype.Face(ttf_path)
        self.face.load_char(
            "d", freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING
        )
        ttf_heigt_d = self.face.glyph.metrics.height

        caminho_d_dst = self._obter_caminho_dst("d", dst_folder)
        if not os.path.exists(caminho_d_dst):
            raise FileNotFoundError(
                f"Config Escala: Arquivo DST para 'd' não encontrado: {caminho_d_dst}"
            )

        letra_d_dst = EmbPattern()
        letra_d_dst.read(caminho_d_dst)
        dst_heigt_d = letra_d_dst.bounds()[3] - letra_d_dst.bounds()[1]

        self.escala = dst_heigt_d / ttf_heigt_d
        # print(f"Config Escala: TTF 'd' height = {ttf_heigt_d}, DST 'd' height = {dst_heigt_d}, Escala = {self.escala:.4f}")
        self.tamanho_espaco = self.tamanhos_disponiveis.get(
            Path(pasta_tamanho_dst).name, {}
        ).get("tamanho_espaco")

    def _carregar_config_fonte(self):
        """Lê o arquivo JSON de configuração da pasta da fonte."""
        config_path = os.path.join(self.font_path, "config.json")
        if not os.path.exists(config_path):
            # Fallback seguro caso você esqueça de criar o JSON em alguma fonte
            raise FileNotFoundError(
                f"Configuração da fonte não encontrada: {config_path}"
            )
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _obter_caminho_dst(self, char, dst_folder):
        ext = "m.DST" if char.isupper() else ".DST"
        nome_arq = "PONTO.DST" if char == "." else f"{char}{ext}"
        caminho_dst = os.path.join(dst_folder, nome_arq)
        return caminho_dst

    def gerar_tentativa(self, nome, dst_folder, espaco_extra=0):
        self.tentativa += 1
        bordado = EmbPattern()
        cursor_x = 0.0
        bordado.add_stitch_absolute(0, 0, 0)  # Início do bordado no ponto zero

        for char in nome:
            if char == " ":
                cursor_x += self.tamanho_espaco
                continue

            self.face.load_char(
                char, freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING
            )
            m = self.face.glyph.metrics

            caminho_dst = self._obter_caminho_dst(char, dst_folder)
            if not os.path.exists(caminho_dst):
                continue

            letra_dst = EmbPattern()
            letra_dst.read(caminho_dst)
            min_x, _, _, max_y = letra_dst.bounds()

            ajuste_x = cursor_x + (m.horiBearingX * self.escala) - min_x
            ajuste_y = (
                (m.height * self.escala) - (m.horiBearingY * self.escala)
            ) - max_y

            letra_dst.translate(ajuste_x, ajuste_y)
            bordado.add_pattern(letra_dst)

            # Atualiza cursor_x para a próxima letra (simplificado, pode ser melhorado)
            cursor_x += (m.horiAdvance * self.escala) + espaco_extra

        for stitch in bordado.get_match_commands(END):
            stitch[2] = NO_COMMAND

        return bordado, cursor_x

    def gerar_nome(self, nome, largura_maxima, espaco_extra=0):
        bordado_final = None

        for key, value in self.tamanhos_disponiveis.items():
            dst_folder = os.path.join(self.font_path, key)
            self._configurar_escala(dst_folder)
            bordado, largura_bordado = self.gerar_tentativa(
                nome, dst_folder, espaco_extra=espaco_extra
            )
            # print(f"Tentativa {self.tentativa}: Gerado bordado para '{nome}' com largura {largura_bordado:.2f}mm usando configuração '{key}'")

            if not largura_maxima or largura_bordado <= largura_maxima:
                bordado_final = bordado
                break

        if bordado_final is None:
            print(
                f"Não foi possível gerar o nome '{nome}' dentro da largura máxima de {largura_maxima}mm. Usando o último tamanho disponível."
            )
            bordado_final = EmbPattern()

        bordado_final.bounds()  # Atualiza os limites do bordado final
        self.centro_textoX = largura_bordado / 2
        self.centro_textoY = (bordado_final.bounds()[3] + bordado_final.bounds()[1]) / 2

        return bordado_final

    def gera_especialidade(
        self,
        bordado_nome: EmbPattern,
        especialidade,
        fonte_especialidade,
        espaco_extra=0,
        espaco_vertical=160,
    ):
        motor_especialidade = MotorBordado(fonte_especialidade)
        # Posicionar a especialidade abaixo do nome principal
        patt_especialidade = motor_especialidade.gerar_nome(
            especialidade, None, espaco_extra=-5
        )  # Ajuste o espaço extra conforme necessário
        # print(f'centro {self.centro_textoX} - centro especialidade {motor_especialidade.centro_textoX}')
        deslocamento_alinhamento_x = (
            self.centro_textoX - motor_especialidade.centro_textoX
        )
        deslocamento_alinhamento_y = (
            (self.centro_textoY - motor_especialidade.centro_textoY) + espaco_vertical
        )  # Ajuste a posição vertical da especialidade conforme necessário
        patt_especialidade.translate(
            deslocamento_alinhamento_x, deslocamento_alinhamento_y
        )  # Ajuste a posição vertical da especialidade conforme necessário
        bordado_nome.add_pattern(patt_especialidade)
        for stitch in bordado_nome.get_match_commands(COLOR_CHANGE):
            stitch[2] = NO_COMMAND

        return bordado_nome

    def incluir_especialidade_pronta(
        self, bordado_nome: EmbPattern, especialidade: str, espaco_vertical=160
    ):
        especialidadepatt = EmbPattern()
        especialidadepatt.read(especialidade)
        espc_centroX = (
            especialidadepatt.bounds()[2] + especialidadepatt.bounds()[0]
        ) / 2
        espc_centroY = (
            especialidadepatt.bounds()[3] + especialidadepatt.bounds()[1]
        ) / 2
        deslocamento_alinhamento_x = self.centro_textoX - espc_centroX
        deslocamento_alinhamento_y = self.centro_textoY - espc_centroY
        especialidadepatt.translate(
            deslocamento_alinhamento_x, deslocamento_alinhamento_y + espaco_vertical
        )  # Ajuste a posição vertical da especialidadepatt conforme necessário
        bordado_nome.add_pattern(especialidadepatt)
        return bordado_nome
