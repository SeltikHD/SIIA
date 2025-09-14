-- Script para inserção de dados de modelo para o SIIA
-- Sistema Inteligente de Irrigação Automática

--* Unidades de Medida *--
INSERT INTO unidade_medida (nome, simbolo) VALUES
('Gramas', 'g'),
('Quilogramas', 'kg'),
('Mililitros', 'ml'),
('Litros', 'L'),
('Milímetros', 'mm'),
('Centímetros', 'cm'),
('Metros', 'm'),
('Partes por milhão', 'ppm'),
('Porcentagem', '%'),
('Unidades', 'un');

--* Grupos de Usuários *--
INSERT INTO grupo (nome, nivel_acesso) VALUES
('Professor', 4),
('Aluno', 2),
('Cuidador do Projeto', 3),
('Visitante', 1);

--* Culturas de Estufa *--
INSERT INTO cultura (nome) VALUES
('Tomate'),
('Alface'),
('Pimentão'),
('Pepino'),
('Rúcula'),
('Manjericão'),
('Salsa'),
('Cebolinha'),
('Morango'),
('Abobrinha');

--* Condições Ideais por Cultura *--
-- Tomate
INSERT INTO condicao_ideal (temperatura_min, temperatura_max, umidade_ar_min, umidade_ar_max, umidade_solo_min, umidade_solo_max, cultura_id)
VALUES (18.0, 25.0, 60.0, 80.0, 70.0, 85.0, (SELECT id FROM cultura WHERE nome = 'Tomate'));

-- Alface
INSERT INTO condicao_ideal (temperatura_min, temperatura_max, umidade_ar_min, umidade_ar_max, umidade_solo_min, umidade_solo_max, cultura_id)
VALUES (15.0, 20.0, 50.0, 70.0, 65.0, 80.0, (SELECT id FROM cultura WHERE nome = 'Alface'));

-- Pimentão
INSERT INTO condicao_ideal (temperatura_min, temperatura_max, umidade_ar_min, umidade_ar_max, umidade_solo_min, umidade_solo_max, cultura_id)
VALUES (20.0, 28.0, 60.0, 75.0, 70.0, 85.0, (SELECT id FROM cultura WHERE nome = 'Pimentão'));

-- Pepino
INSERT INTO condicao_ideal (temperatura_min, temperatura_max, umidade_ar_min, umidade_ar_max, umidade_solo_min, umidade_solo_max, cultura_id)
VALUES (18.0, 24.0, 70.0, 85.0, 75.0, 90.0, (SELECT id FROM cultura WHERE nome = 'Pepino'));

-- Rúcula
INSERT INTO condicao_ideal (temperatura_min, temperatura_max, umidade_ar_min, umidade_ar_max, umidade_solo_min, umidade_solo_max, cultura_id)
VALUES (12.0, 18.0, 50.0, 65.0, 60.0, 75.0, (SELECT id FROM cultura WHERE nome = 'Rúcula'));

-- Manjericão
INSERT INTO condicao_ideal (temperatura_min, temperatura_max, umidade_ar_min, umidade_ar_max, umidade_solo_min, umidade_solo_max, cultura_id)
VALUES (18.0, 25.0, 55.0, 70.0, 65.0, 80.0, (SELECT id FROM cultura WHERE nome = 'Manjericão'));

-- Salsa
INSERT INTO condicao_ideal (temperatura_min, temperatura_max, umidade_ar_min, umidade_ar_max, umidade_solo_min, umidade_solo_max, cultura_id)
VALUES (15.0, 22.0, 50.0, 70.0, 60.0, 75.0, (SELECT id FROM cultura WHERE nome = 'Salsa'));

-- Cebolinha
INSERT INTO condicao_ideal (temperatura_min, temperatura_max, umidade_ar_min, umidade_ar_max, umidade_solo_min, umidade_solo_max, cultura_id)
VALUES (15.0, 25.0, 50.0, 70.0, 60.0, 80.0, (SELECT id FROM cultura WHERE nome = 'Cebolinha'));

-- Morango
INSERT INTO condicao_ideal (temperatura_min, temperatura_max, umidade_ar_min, umidade_ar_max, umidade_solo_min, umidade_solo_max, cultura_id)
VALUES (15.0, 22.0, 60.0, 75.0, 70.0, 85.0, (SELECT id FROM cultura WHERE nome = 'Morango'));

-- Abobrinha
INSERT INTO condicao_ideal (temperatura_min, temperatura_max, umidade_ar_min, umidade_ar_max, umidade_solo_min, umidade_solo_max, cultura_id)
VALUES (18.0, 25.0, 55.0, 75.0, 65.0, 80.0, (SELECT id FROM cultura WHERE nome = 'Abobrinha'));

--* Fertilizantes Comuns *--
INSERT INTO fertilizante (nome, unidade_medida_id) VALUES
('NPK 10-10-10', (SELECT id FROM unidade_medida WHERE simbolo = 'g')),
('NPK 20-05-20', (SELECT id FROM unidade_medida WHERE simbolo = 'g')),
('Superfosfato Simples', (SELECT id FROM unidade_medida WHERE simbolo = 'g')),
('Sulfato de Potássio', (SELECT id FROM unidade_medida WHERE simbolo = 'g')),
('Ureia', (SELECT id FROM unidade_medida WHERE simbolo = 'g')),
('Sulfato de Amônio', (SELECT id FROM unidade_medida WHERE simbolo = 'g')),
('Cloreto de Potássio', (SELECT id FROM unidade_medida WHERE simbolo = 'g')),
('Nitrato de Cálcio', (SELECT id FROM unidade_medida WHERE simbolo = 'g')),
('Ácido Bórico', (SELECT id FROM unidade_medida WHERE simbolo = 'g')),
('Sulfato de Magnésio', (SELECT id FROM unidade_medida WHERE simbolo = 'g'));

--* Relação Fertilizante-Cultura com Quantidades Recomendadas *--
-- NPK 10-10-10 para várias culturas
INSERT INTO fertilizante_cultura (fertilizante_id, cultura_id, quantidade_recomendada) VALUES
((SELECT id FROM fertilizante WHERE nome = 'NPK 10-10-10'), (SELECT id FROM cultura WHERE nome = 'Tomate'), 50.0),
((SELECT id FROM fertilizante WHERE nome = 'NPK 10-10-10'), (SELECT id FROM cultura WHERE nome = 'Alface'), 30.0),
((SELECT id FROM fertilizante WHERE nome = 'NPK 10-10-10'), (SELECT id FROM cultura WHERE nome = 'Pimentão'), 45.0),
((SELECT id FROM fertilizante WHERE nome = 'NPK 10-10-10'), (SELECT id FROM cultura WHERE nome = 'Pepino'), 40.0);

-- NPK 20-05-20 para culturas que precisam mais nitrogênio
INSERT INTO fertilizante_cultura (fertilizante_id, cultura_id, quantidade_recomendada) VALUES
((SELECT id FROM fertilizante WHERE nome = 'NPK 20-05-20'), (SELECT id FROM cultura WHERE nome = 'Rúcula'), 25.0),
((SELECT id FROM fertilizante WHERE nome = 'NPK 20-05-20'), (SELECT id FROM cultura WHERE nome = 'Manjericão'), 30.0),
((SELECT id FROM fertilizante WHERE nome = 'NPK 20-05-20'), (SELECT id FROM cultura WHERE nome = 'Salsa'), 25.0),
((SELECT id FROM fertilizante WHERE nome = 'NPK 20-05-20'), (SELECT id FROM cultura WHERE nome = 'Cebolinha'), 20.0);

-- Nitrato de Cálcio para frutas
INSERT INTO fertilizante_cultura (fertilizante_id, cultura_id, quantidade_recomendada) VALUES
((SELECT id FROM fertilizante WHERE nome = 'Nitrato de Cálcio'), (SELECT id FROM cultura WHERE nome = 'Tomate'), 35.0),
((SELECT id FROM fertilizante WHERE nome = 'Nitrato de Cálcio'), (SELECT id FROM cultura WHERE nome = 'Morango'), 30.0),
((SELECT id FROM fertilizante WHERE nome = 'Nitrato de Cálcio'), (SELECT id FROM cultura WHERE nome = 'Abobrinha'), 40.0);

-- Superfosfato para enraizamento
INSERT INTO fertilizante_cultura (fertilizante_id, cultura_id, quantidade_recomendada) VALUES
((SELECT id FROM fertilizante WHERE nome = 'Superfosfato Simples'), (SELECT id FROM cultura WHERE nome = 'Morango'), 25.0),
((SELECT id FROM fertilizante WHERE nome = 'Superfosfato Simples'), (SELECT id FROM cultura WHERE nome = 'Tomate'), 30.0),
((SELECT id FROM fertilizante WHERE nome = 'Superfosfato Simples'), (SELECT id FROM cultura WHERE nome = 'Pimentão'), 28.0);

-- Sulfato de Potássio para qualidade dos frutos
INSERT INTO fertilizante_cultura (fertilizante_id, cultura_id, quantidade_recomendada) VALUES
((SELECT id FROM fertilizante WHERE nome = 'Sulfato de Potássio'), (SELECT id FROM cultura WHERE nome = 'Tomate'), 25.0),
((SELECT id FROM fertilizante WHERE nome = 'Sulfato de Potássio'), (SELECT id FROM cultura WHERE nome = 'Morango'), 20.0),
((SELECT id FROM fertilizante WHERE nome = 'Sulfato de Potássio'), (SELECT id FROM cultura WHERE nome = 'Abobrinha'), 30.0);

--* Sessões da Estufa *--
INSERT INTO sessao (nome, cultura_id) VALUES
('Seção A - Tomates', (SELECT id FROM cultura WHERE nome = 'Tomate')),
('Seção B - Folhosas', (SELECT id FROM cultura WHERE nome = 'Alface')),
('Seção C - Temperos', (SELECT id FROM cultura WHERE nome = 'Manjericão')),
('Seção D - Frutas', (SELECT id FROM cultura WHERE nome = 'Morango'));

--* Dados de exemplo (dados periódicos) *--
-- Inserindo alguns dados de exemplo para cada sessão
-- Seção A - Tomates
INSERT INTO dado_periodico (temperatura, umidade_ar, umidade_solo, cultura_id, sessao_id, exaustor_ligado)
VALUES 
(22.5, 72.0, 78.0, (SELECT id FROM cultura WHERE nome = 'Tomate'), (SELECT id FROM sessao WHERE nome = 'Seção A - Tomates'), false),
(21.8, 68.5, 75.5, (SELECT id FROM cultura WHERE nome = 'Tomate'), (SELECT id FROM sessao WHERE nome = 'Seção A - Tomates'), false),
(23.2, 75.0, 80.0, (SELECT id FROM cultura WHERE nome = 'Tomate'), (SELECT id FROM sessao WHERE nome = 'Seção A - Tomates'), true);

-- Seção B - Folhosas
INSERT INTO dado_periodico (temperatura, umidade_ar, umidade_solo, cultura_id, sessao_id, exaustor_ligado)
VALUES 
(17.5, 62.0, 72.0, (SELECT id FROM cultura WHERE nome = 'Alface'), (SELECT id FROM sessao WHERE nome = 'Seção B - Folhosas'), false),
(18.2, 58.5, 70.5, (SELECT id FROM cultura WHERE nome = 'Alface'), (SELECT id FROM sessao WHERE nome = 'Seção B - Folhosas'), false),
(16.8, 65.0, 74.0, (SELECT id FROM cultura WHERE nome = 'Alface'), (SELECT id FROM sessao WHERE nome = 'Seção B - Folhosas'), false);

-- Seção C - Temperos
INSERT INTO dado_periodico (temperatura, umidade_ar, umidade_solo, cultura_id, sessao_id, exaustor_ligado)
VALUES 
(21.0, 63.0, 72.0, (SELECT id FROM cultura WHERE nome = 'Manjericão'), (SELECT id FROM sessao WHERE nome = 'Seção C - Temperos'), false),
(22.5, 66.5, 75.5, (SELECT id FROM cultura WHERE nome = 'Manjericão'), (SELECT id FROM sessao WHERE nome = 'Seção C - Temperos'), false),
(20.8, 61.0, 70.0, (SELECT id FROM cultura WHERE nome = 'Manjericão'), (SELECT id FROM sessao WHERE nome = 'Seção C - Temperos'), false);

-- Seção D - Frutas
INSERT INTO dado_periodico (temperatura, umidade_ar, umidade_solo, cultura_id, sessao_id, exaustor_ligado)
VALUES 
(18.5, 67.0, 77.0, (SELECT id FROM cultura WHERE nome = 'Morango'), (SELECT id FROM sessao WHERE nome = 'Seção D - Frutas'), false),
(19.2, 70.5, 80.5, (SELECT id FROM cultura WHERE nome = 'Morango'), (SELECT id FROM sessao WHERE nome = 'Seção D - Frutas'), false),
(17.8, 64.0, 75.0, (SELECT id FROM cultura WHERE nome = 'Morango'), (SELECT id FROM sessao WHERE nome = 'Seção D - Frutas'), false);

--* Notificações de exemplo *--
INSERT INTO notificacao (titulo, mensagem) VALUES
('Sistema Iniciado', 'O sistema SIIA foi iniciado com sucesso e está monitorando as condições da estufa.'),
('Temperatura Alta', 'A temperatura na Seção A excedeu os limites ideais para cultivo de tomates.'),
('Irrigação Programada', 'Sistema de irrigação será ativado automaticamente em 30 minutos.'),
('Manutenção Preventiva', 'Lembrete: Verificar sensores de umidade do solo na Seção B.');

-- Informações adicionais no log
INSERT INTO log (usuario_id, mensagem) VALUES
((SELECT id FROM usuario WHERE email = 'admin@siia.ifpb.edu.br'), 'Sistema inicializado com dados de modelo.'),
((SELECT id FROM usuario WHERE email = 'admin@siia.ifpb.edu.br'), 'Configuração de culturas e condições ideais carregada.'),
((SELECT id FROM usuario WHERE email = 'admin@siia.ifpb.edu.br'), 'Fertilizantes e sessões configurados com sucesso.');