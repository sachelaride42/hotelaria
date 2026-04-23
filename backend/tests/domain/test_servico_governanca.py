import pytest
from backend.src.domain.models.quarto import Quarto, StatusLimpeza, StatusOcupacao
from backend.src.domain.services.servico_governanca import ServicoGovernanca


def test_filtrar_quartos_para_limpeza_retorna_apenas_sujos():
    """Retorna apenas quartos com status SUJO na listagem de limpeza."""
    limpo = Quarto(numero="101", andar=1, tipo_quarto_id=1, status_limpeza=StatusLimpeza.LIMPO)
    sujo = Quarto(numero="102", andar=1, tipo_quarto_id=1, status_limpeza=StatusLimpeza.SUJO)
    sujo2 = Quarto(numero="103", andar=1, tipo_quarto_id=1, status_limpeza=StatusLimpeza.SUJO)

    resultado = ServicoGovernanca.filtrar_quartos_para_limpeza([limpo, sujo, sujo2])

    assert len(resultado) == 2
    assert all(q.status_limpeza == StatusLimpeza.SUJO for q in resultado)


def test_filtrar_quartos_para_limpeza_lista_vazia_quando_todos_limpos():
    """Retorna lista vazia quando todos os quartos estão limpos."""
    limpo1 = Quarto(numero="101", andar=1, tipo_quarto_id=1, status_limpeza=StatusLimpeza.LIMPO)
    limpo2 = Quarto(numero="102", andar=1, tipo_quarto_id=1, status_limpeza=StatusLimpeza.LIMPO)

    resultado = ServicoGovernanca.filtrar_quartos_para_limpeza([limpo1, limpo2])

    assert resultado == []


def test_validar_solicitacao_limpeza_quarto_ocupado_levanta_erro():
    """Impede solicitação de limpeza em quarto ocupado."""
    quarto = Quarto(numero="201", andar=2, tipo_quarto_id=1, status_ocupacao=StatusOcupacao.OCUPADO)

    with pytest.raises(ValueError, match="está ocupado"):
        ServicoGovernanca.validar_solicitacao_limpeza(quarto)


def test_validar_solicitacao_limpeza_quarto_ja_sujo_levanta_erro():
    """Impede nova solicitação de limpeza em quarto já marcado como SUJO."""
    quarto = Quarto(numero="202", andar=2, tipo_quarto_id=1, status_limpeza=StatusLimpeza.SUJO)

    with pytest.raises(ValueError, match="já está marcado para limpeza"):
        ServicoGovernanca.validar_solicitacao_limpeza(quarto)


def test_validar_solicitacao_limpeza_quarto_livre_limpo_nao_levanta_erro():
    """Aceita solicitação de limpeza em quarto LIVRE e LIMPO."""
    quarto = Quarto(numero="203", andar=2, tipo_quarto_id=1,
                    status_ocupacao=StatusOcupacao.LIVRE, status_limpeza=StatusLimpeza.LIMPO)

    ServicoGovernanca.validar_solicitacao_limpeza(quarto)


def test_validar_solicitacao_limpeza_quarto_manutencao_nao_levanta_erro():
    """Aceita solicitação de limpeza em quarto em MANUTENCAO."""
    quarto = Quarto(numero="204", andar=2, tipo_quarto_id=1,
                    status_ocupacao=StatusOcupacao.MANUTENCAO, status_limpeza=StatusLimpeza.LIMPO)

    ServicoGovernanca.validar_solicitacao_limpeza(quarto)


def test_validar_conclusao_limpeza_quarto_limpo_levanta_erro():
    """Impede conclusão de limpeza em quarto que já está LIMPO."""
    quarto = Quarto(numero="301", andar=3, tipo_quarto_id=1, status_limpeza=StatusLimpeza.LIMPO)

    with pytest.raises(ValueError, match="já está limpo"):
        ServicoGovernanca.validar_conclusao_limpeza(quarto)


def test_validar_conclusao_limpeza_quarto_sujo_nao_levanta_erro():
    """Aceita conclusão de limpeza em quarto SUJO."""
    quarto = Quarto(numero="302", andar=3, tipo_quarto_id=1, status_limpeza=StatusLimpeza.SUJO)

    ServicoGovernanca.validar_conclusao_limpeza(quarto)
