# Projeto de Hotelaria
Projeto realizado a partir de requisitos reais, feito como projeto de conclusão do curso de Engenharia de Software. O objetivo do projeto é automatizar o fluxo de trabalho da recepção de um hotel, o que inclui os fluxos de reserva, check-in, check-out, gastos, etc.

## Configuração
1. Copie o arquivo de exemplo:
cp .env.example backend/.env
2. Edite o `backend/.env` com suas credenciais reais
3. Gere uma SECRET_KEY segura:
python -c "import secrets; print(secrets.token_hex(32))"
