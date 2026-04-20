import pytest
from backend.src.domain.models.quarto import Quarto, StatusLimpeza, StatusOcupacao
from backend.src.domain.services.servico_governanca import ServicoGovernanca


def test_filtrar_quartos_para_limpeza_retorna_apenas_sujos():
    limpo = Quarto(numero="101", andar=1, tipo_quarto_id=1, status_limpeza=StatusLimpeza.LIMPO)
    sujo = Quarto(numero="102", andar=1, tipo_quarto_id=1, status_limpeza=StatusLimpeza.SUJO)
    sujo2 = Quarto(numero="103", andar=1, tipo_quarto_id=1, status_limpeza=StatusLimpeza.SUJO)

    resultado = ServicoGovernanca.filtrar_quartos_para_limpeza([limpo, sujo, sujo2])

    assert len(resultado) == 2
    assert all(q.status_limpeza == StatusLimpeza.SUJO for q in resultado)


def test_filtrar_quartos_para_limpeza_lista_vazia_quando_todos_limpos():
    limpo1 = Quarto(numero="101", andar=1, tipo_quarto_id=1, status_limpeza=StatusLimpeza.LIMPO)
    limpo2 = Quarto(numero="102", andar=1, tipo_quarto_id=1, status_limpeza=StatusLimpeza.LIMPO)

    resultado = ServicoGovernanca.filtrar_quartos_para_limpeza([limpo1, limpo2])

    assert resultado == []


def test_validar_solicitacao_limpeza_quarto_ocupado_levanta_erro():
    quarto = Quarto(numero="201", andar=2, tipo_quarto_id=1, status_ocupacao=StatusOcupacao.OCUPADO)

    with pytest.raises(ValueError, match="está ocupado"):
        ServicoGovernanca.validar_solicitacao_limpeza(quarto)


def test_validar_solicitacao_limpeza_quarto_ja_sujo_levanta_erro():
    quarto = Quarto(numero="202", andar=2, tipo_quarto_id=1, status_limpeza=StatusLimpeza.SUJO)

    with pytest.raises(ValueError, match="já está marcado para limpeza"):
        ServicoGovernanca.validar_solicitacao_limpeza(quarto)


def test_validar_solicitacao_limpeza_quarto_livre_limpo_nao_levanta_erro():
    quarto = Quarto(numero="203", andar=2, tipo_quarto_id=1,
                    status_ocupacao=StatusOcupacao.LIVRE, status_limpeza=StatusLimpeza.LIMPO)

    ServicoGovernanca.validar_solicitacao_limpeza(quarto)  # não deve lançar


def test_validar_solicitacao_limpeza_quarto_manutencao_nao_levanta_erro():
    quarto = Quarto(numero="204", andar=2, tipo_quarto_id=1,
                    status_ocupacao=StatusOcupacao.MANUTENCAO, status_limpeza=StatusLimpeza.LIMPO)

    ServicoGovernanca.validar_solicitacao_limpeza(quarto)  # manutenção é permitido


def test_validar_conclusao_limpeza_quarto_limpo_levanta_erro():
    quarto = Quarto(numero="301", andar=3, tipo_quarto_id=1, status_limpeza=StatusLimpeza.LIMPO)

    with pytest.raises(ValueError, match="já está limpo"):
        ServicoGovernanca.validar_conclusao_limpeza(quarto)


def test_validar_conclusao_limpeza_quarto_sujo_nao_levanta_erro():
    quarto = Quarto(numero="302", andar=3, tipo_quarto_id=1, status_limpeza=StatusLimpeza.SUJO)

    ServicoGovernanca.validar_conclusao_limpeza(quarto)  # não deve lançar
