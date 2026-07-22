// Generated semantic nodes and relations. Embeddings are imported from Parquet.
CREATE CONSTRAINT behavior_id IF NOT EXISTS FOR (n:HanhVi) REQUIRE n.id IS UNIQUE;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:9c573eb0a3aede982556a01d"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"32833\", \"article_id\": \"vbpl:32833:chapter:I:1:article:12:12\", \"text\": \"Khoản 1. Lấn, chiếm, hủy hoại đất đai.\", \"canonical_text\": \"Lấn, chiếm, hủy hoại đất đai\", \"action\": \"lấn, chiếm, hủy hoại\", \"object\": \"đất đai\", \"evidence\": \"Khoản 1. Lấn, chiếm, hủy hoại đất đai.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 12 | Lấn, chiếm, hủy hoại đất đai\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:32833:chapter:I:1:article:12:12:clause:1:1"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:487e6a6951122f576c5f614d"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"32833\", \"article_id\": \"vbpl:32833:chapter:I:1:article:12:12\", \"text\": \"Khoản 2. Vi phạm quy hoạch, kế hoạch sử dụng đất đã được công bố.\", \"canonical_text\": \"Vi phạm quy hoạch, kế hoạch sử dụng đất đã được công bố\", \"action\": \"vi phạm quy hoạch, kế hoạch sử dụng đất\", \"object\": \"quy hoạch, kế hoạch sử dụng đất\", \"evidence\": \"Khoản 2. Vi phạm quy hoạch, kế hoạch sử dụng đất đã được công bố.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 12 | Vi phạm quy hoạch, kế hoạch sử dụng đất đã được công bố\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:32833:chapter:I:1:article:12:12:clause:2:2"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:8d54e16ccca38ba16fb7ac8e"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"32833\", \"article_id\": \"vbpl:32833:chapter:I:1:article:12:12\", \"text\": \"Khoản 3. Không sử dụng đất, sử dụng đất không đúng mục đích.\", \"canonical_text\": \"Không sử dụng đất, sử dụng đất không đúng mục đích\", \"action\": \"không sử dụng đất; sử dụng đất không đúng mục đích\", \"object\": \"đất\", \"evidence\": \"Khoản 3. Không sử dụng đất, sử dụng đất không đúng mục đích.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 12 | Không sử dụng đất, sử dụng đất không đúng mục đích\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:32833:chapter:I:1:article:12:12:clause:3:3"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:4d1e9bac0e1984c5dfd8871c"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"32833\", \"article_id\": \"vbpl:32833:chapter:I:1:article:12:12\", \"text\": \"Khoản 4. Không thực hiện đúng quy định của pháp luật khi thực hiện quyền của người sử dụng đất.\", \"canonical_text\": \"Không thực hiện đúng quy định khi thực hiện quyền của người sử dụng đất\", \"action\": \"không thực hiện đúng quy định của pháp luật\", \"object\": \"quyền của người sử dụng đất\", \"evidence\": \"Khoản 4. Không thực hiện đúng quy định của pháp luật khi thực hiện quyền của người sử dụng đất.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 12 | Không thực hiện đúng quy định khi thực hiện quyền của người sử dụng đất\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:32833:chapter:I:1:article:12:12:clause:4:4"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:6eeadcc9159d6d5622e2e351"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"32833\", \"article_id\": \"vbpl:32833:chapter:I:1:article:12:12\", \"text\": \"Khoản 5. Nhận chuyển quyền sử dụng đất nông nghiệp vượt hạn mức đối với hộ gia đình, cá nhân theo quy định của Luật này.\", \"canonical_text\": \"Nhận chuyển quyền sử dụng đất nông nghiệp vượt hạn mức\", \"action\": \"nhận chuyển quyền sử dụng đất nông nghiệp vượt hạn mức\", \"object\": \"quyền sử dụng đất nông nghiệp\", \"condition\": \"theo quy định của Luật này\", \"evidence\": \"Khoản 5. Nhận chuyển quyền sử dụng đất nông nghiệp vượt hạn mức đối với hộ gia đình, cá nhân theo quy định của Luật này.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 12 | Nhận chuyển quyền sử dụng đất nông nghiệp vượt hạn mức\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:32833:chapter:I:1:article:12:12:clause:5:5"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:b8d85c56c744d8b8ab9b2c1d"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"32833\", \"article_id\": \"vbpl:32833:chapter:I:1:article:12:12\", \"text\": \"Khoản 6. Sử dụng đất, thực hiện giao dịch về quyền sử dụng đất mà không đăng ký với cơ quan nhà nước có thẩm quyền.\", \"canonical_text\": \"Sử dụng đất; thực hiện giao dịch về quyền sử dụng đất mà không đăng ký\", \"action\": \"sử dụng đất; thực hiện giao dịch về quyền sử dụng đất\", \"object\": \"quyền sử dụng đất\", \"condition\": \"không đăng ký với cơ quan nhà nước có thẩm quyền\", \"evidence\": \"Khoản 6. Sử dụng đất, thực hiện giao dịch về quyền sử dụng đất mà không đăng ký với cơ quan nhà nước có thẩm quyền.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 12 | Sử dụng đất; thực hiện giao dịch về quyền sử dụng đất mà không đăng ký\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:32833:chapter:I:1:article:12:12:clause:6:6"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:37b37a3c8ec33d78cd3dac5a"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"32833\", \"article_id\": \"vbpl:32833:chapter:I:1:article:12:12\", \"text\": \"Khoản 7. Không thực hiện hoặc thực hiện không đầy đủ nghĩa vụ tài chính đối với Nhà nước.\", \"canonical_text\": \"Không thực hiện hoặc thực hiện không đầy đủ nghĩa vụ tài chính\", \"action\": \"không thực hiện hoặc thực hiện không đầy đủ nghĩa vụ tài chính\", \"object\": \"nghĩa vụ tài chính đối với Nhà nước\", \"evidence\": \"Khoản 7. Không thực hiện hoặc thực hiện không đầy đủ nghĩa vụ tài chính đối với Nhà nước.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 12 | Không thực hiện hoặc thực hiện không đầy đủ nghĩa vụ tài chính\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:32833:chapter:I:1:article:12:12:clause:7:7"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:f0f8b27533f0bdc3e8ad82e6"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"32833\", \"article_id\": \"vbpl:32833:chapter:I:1:article:12:12\", \"text\": \"Khoản 8. Lợi dụng chức vụ, quyền hạn để làm trái quy định về quản lý đất đai.\", \"canonical_text\": \"Lợi dụng chức vụ, quyền hạn để làm trái quy định về quản lý đất đai\", \"action\": \"lợi dụng chức vụ, quyền hạn\", \"object\": \"quy định về quản lý đất đai\", \"evidence\": \"Khoản 8. Lợi dụng chức vụ, quyền hạn để làm trái quy định về quản lý đất đai.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 12 | Lợi dụng chức vụ, quyền hạn để làm trái quy định về quản lý đất đai\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:32833:chapter:I:1:article:12:12:clause:8:8"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:8d5a5364b801c641ea96ab98"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"32833\", \"article_id\": \"vbpl:32833:chapter:I:1:article:12:12\", \"text\": \"Khoản 9. Không cung cấp hoặc cung cấp thông tin về đất đai không chính xác theo quy định của pháp luật.\", \"canonical_text\": \"Không cung cấp hoặc cung cấp thông tin về đất đai không chính xác\", \"action\": \"không cung cấp hoặc cung cấp thông tin về đất đai\", \"object\": \"thông tin về đất đai\", \"condition\": \"không chính xác theo quy định của pháp luật\", \"evidence\": \"Khoản 9. Không cung cấp hoặc cung cấp thông tin về đất đai không chính xác theo quy định của pháp luật.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 12 | Không cung cấp hoặc cung cấp thông tin về đất đai không chính xác\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:32833:chapter:I:1:article:12:12:clause:9:9"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:1241a08fdeacdb6b470d825d"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"32833\", \"article_id\": \"vbpl:32833:chapter:I:1:article:12:12\", \"text\": \"Khoản 10. Cản trở, gây khó khăn đối với việc thực hiện quyền của người sử dụng đất theo quy định của pháp luật.\", \"canonical_text\": \"Cản trợ, gây khó khăn đối với việc thực hiện quyền của người sử dụng đất\", \"action\": \"cản trở, gây khó khăn\", \"object\": \"việc thực hiện quyền của người sử dụng đất\", \"condition\": \"theo quy định của pháp luật\", \"evidence\": \"Khoản 10. Cản trở, gây khó khăn đối với việc thực hiện quyền của người sử dụng đất theo quy định của pháp luật.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 12 | Cản trợ, gây khó khăn đối với việc thực hiện quyền của người sử dụng đất\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:32833:chapter:I:1:article:12:12:clause:10:10"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:b4a4e14dbdda9310546c1bac"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"177815\", \"article_id\": \"vbpl:177815:chapter:I:1:article:11:11\", \"text\": \"Lấn đất, chiếm đất, hủy hoại đất.\", \"canonical_text\": \"Lấn đất, chiếm đất, hủy hoại đất.\", \"action\": \"Lấn đất, chiếm đất, hủy hoại đất\", \"object\": \"đất\", \"evidence\": \"Lấn đất, chiếm đất, hủy hoại đất.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 11 | Lấn đất, chiếm đất, hủy hoại đất.\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:177815:chapter:I:1:article:11:11:clause:1:1"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:6a21cd77545f75781a4f54a8"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"177815\", \"article_id\": \"vbpl:177815:chapter:I:1:article:11:11\", \"text\": \"Vi phạm quy định của pháp luật về quản lý nhà nước về đất đai.\", \"canonical_text\": \"Vi phạm quy định về quản lý đất đai.\", \"action\": \"Vi phạm\", \"object\": \"quy định về quản lý đất đai\", \"evidence\": \"Vi phạm quy định của pháp luật về quản lý nhà nước về đất đai.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 11 | Vi phạm quy định về quản lý đất đai.\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:177815:chapter:I:1:article:11:11:clause:2:2"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:5f5d2b078cb8366f7eb38728"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"177815\", \"article_id\": \"vbpl:177815:chapter:I:1:article:11:11\", \"text\": \"Vi phạm chính sách về đất đai đối với đồng bào dân tộc thiểu số.\", \"canonical_text\": \"Vi phạm chính sách đất đai đối với đồng bào dân tộc thiểu số.\", \"action\": \"Vi phạm\", \"object\": \"chính sách đất đai đối với đồng bào dân tộc thiểu số\", \"evidence\": \"Vi phạm chính sách về đất đai đối với đồng bào dân tộc thiểu số.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 11 | Vi phạm chính sách đất đai đối với đồng bào dân tộc thiểu số.\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:177815:chapter:I:1:article:11:11:clause:3:3"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:9b11c21ef0c035fa72984a62"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"177815\", \"article_id\": \"vbpl:177815:chapter:I:1:article:11:11\", \"text\": \"Lợi dụng chức vụ, quyền hạn để làm trái quy định của pháp luật về quản lý đất đai.\", \"canonical_text\": \"Lợi dụng chức vụ, quyền hạn để làm trái quy định của pháp luật về quản lý đất đai.\", \"action\": \"Lợi dụng chức vụ, quyền hạn để làm trái quy định pháp luật về quản lý đất đai\", \"object\": \"quy định của pháp luật về quản lý đất đai\", \"evidence\": \"Lợi dụng chức vụ, quyền hạn để làm trái quy định của pháp luật về quản lý đất đai.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 11 | Lợi dụng chức vụ, quyền hạn để làm trái quy định của pháp luật về quản lý đất đai.\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:177815:chapter:I:1:article:11:11:clause:4:4"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:346a38c28f14d902ba9f4ba4"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"177815\", \"article_id\": \"vbpl:177815:chapter:I:1:article:11:11\", \"text\": \"Không cung cấp thông tin hoặc cung cấp thông tin đất đai không chính xác, không đáp ứng yêu cầu về thời hạn theo quy định của pháp luật.\", \"canonical_text\": \"Không cung cấp thông tin đất đai đúng hoặc không đáp ứng yêu cầu về thời hạn.\", \"action\": \"Không cung cấp thông tin đất đai không chính xác, không đáp ứng yêu cầu về thời hạn\", \"object\": \"thông tin đất đai\", \"evidence\": \"Không cung cấp thông tin hoặc cung cấp thông tin đất đai không chính xác, không đáp ứng yêu cầu về thời hạn theo quy định của pháp luật.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 11 | Không cung cấp thông tin đất đai đúng hoặc không đáp ứng yêu cầu về thời hạn.\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:177815:chapter:I:1:article:11:11:clause:5:5"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:5799648a5e459c1146ece7b9"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"177815\", \"article_id\": \"vbpl:177815:chapter:I:1:article:11:11\", \"text\": \"Không ngăn chặn, không xử lý hành vi vi phạm pháp luật về đất đai.\", \"canonical_text\": \"Không ngăn chặn và không xử lý hành vi vi phạm pháp luật về đất đai.\", \"action\": \"Không ngăn chặn, không xử lý\", \"object\": \"hành vi vi phạm pháp luật về đất đai\", \"evidence\": \"Không ngăn chặn, không xử lý hành vi vi phạm pháp luật về đất đai.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 11 | Không ngăn chặn và không xử lý hành vi vi phạm pháp luật về đất đai.\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:177815:chapter:I:1:article:11:11:clause:6:6"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:c707dda3c3c08672fa66c1d7"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"177815\", \"article_id\": \"vbpl:177815:chapter:I:1:article:11:11\", \"text\": \"Không thực hiện đúng quy định của pháp luật khi thực hiện quyền của người sử dụng đất.\", \"canonical_text\": \"Không thực hiện đúng quy định pháp luật khi thực hiện quyền của người sử dụng đất.\", \"action\": \"Không thực hiện đúng quy định của pháp luật\", \"object\": \"quyền của người sử dụng đất\", \"evidence\": \"Không thực hiện đúng quy định của pháp luật khi thực hiện quyền của người sử dụng đất.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 11 | Không thực hiện đúng quy định pháp luật khi thực hiện quyền của người sử dụng đất.\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:177815:chapter:I:1:article:11:11:clause:7:7"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:36415ef2e825e2cb1b1ef528"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"177815\", \"article_id\": \"vbpl:177815:chapter:I:1:article:11:11\", \"text\": \"Sử dụng đất, thực hiện giao dịch về quyền sử dụng đất mà không đăng ký với cơ quan có thẩm quyền.\", \"canonical_text\": \"Sử dụng đất hoặc giao dịch về quyền sử dụng đất mà không đăng ký với cơ quan có thẩm quyền.\", \"action\": \"Sử dụng đất; thực hiện giao dịch về quyền sử dụng đất mà không đăng ký\", \"object\": \"quyền sử dụng đất và giao dịch về quyền sử dụng đất\", \"evidence\": \"Sử dụng đất, thực hiện giao dịch về quyền sử dụng đất mà không đăng ký với cơ quan có thẩm quyền.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 11 | Sử dụng đất hoặc giao dịch về quyền sử dụng đất mà không đăng ký với cơ quan có thẩm quyền.\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:177815:chapter:I:1:article:11:11:clause:8:8"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:bf93b4b4d04c07824bdabd02"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"177815\", \"article_id\": \"vbpl:177815:chapter:I:1:article:11:11\", \"text\": \"Không thực hiện hoặc thực hiện không đầy đủ nghĩa vụ tài chính đối với Nhà nước.\", \"canonical_text\": \"Không thực hiện hoặc thực hiện không đầy đủ nghĩa vụ tài chính với Nhà nước.\", \"action\": \"Không thực hiện hoặc thực hiện không đầy đủ nghĩa vụ tài chính\", \"object\": \"nghĩa vụ tài chính đối với Nhà nước\", \"evidence\": \"Không thực hiện hoặc thực hiện không đầy đủ nghĩa vụ tài chính đối với Nhà nước.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 11 | Không thực hiện hoặc thực hiện không đầy đủ nghĩa vụ tài chính với Nhà nước.\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:177815:chapter:I:1:article:11:11:clause:9:9"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:4d0e2b47cfd83d8be5563cd6"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"177815\", \"article_id\": \"vbpl:177815:chapter:I:1:article:11:11\", \"text\": \"Cản trở, gây khó khăn đối với việc sử dụng đất, việc thực hiện quyền của người sử dụng đất theo quy định của pháp luật.\", \"canonical_text\": \"Cản trở, gây khó khăn cho việc sử dụng đất và thực hiện quyền của người sử dụng đất.\", \"action\": \"Cản trở, gây khó khăn\", \"object\": \"việc sử dụng đất và thực hiện quyền của người sử dụng đất\", \"evidence\": \"Cản trở, gây khó khăn đối với việc sử dụng đất, việc thực hiện quyền của người sử dụng đất theo quy định của pháp luật.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 11 | Cản trở, gây khó khăn cho việc sử dụng đất và thực hiện quyền của người sử dụng đất.\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:177815:chapter:I:1:article:11:11:clause:10:10"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MERGE (h:HanhVi:SemanticNode {id: "hanh_vi:3e4f2768f7c6d0a027a6ae8f"})
SET h += apoc.convert.fromJsonMap("{\"document_id\": \"177815\", \"article_id\": \"vbpl:177815:chapter:I:1:article:11:11\", \"text\": \"Phân biệt đối xử về giới trong quản lý, sử dụng đất đai.\", \"canonical_text\": \"Phân biệt đối xử về giới trong quản lý, sử dụng đất đai.\", \"action\": \"Phân biệt đối xử về giới\", \"object\": \"quản lý, sử dụng đất đai\", \"evidence\": \"Phân biệt đối xử về giới trong quản lý, sử dụng đất đai.\", \"confidence\": 1.0, \"status\": \"PROPOSED\", \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"embedding_text\": \"Hành vi bị nghiêm cấm theo Điều 11 | Phân biệt đối xử về giới trong quản lý, sử dụng đất đai.\"}")
WITH h MATCH (source:LegalNode {id: "vbpl:177815:chapter:I:1:article:11:11:clause:11:11"})
MERGE (h)-[r:VI_PHAM]->(source)
SET r.status = h.status, r.confidence = h.confidence, r.method = h.method, r.model = h.model, r.evidence = h.evidence;

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XVI:16:section:2:2:article:254:3:clause:3:3"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:VI:6:section:1:1:article:64:4:clause:1:1:point:i:9"})
MERGE (source)-[r:DAN_CHIEU]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"VERIFIED\", \"confidence\": 1.0, \"method\": \"RULE\", \"evidence_new\": \"điểm i khoản 1 Điều 64 của Luật Đất đai số 45/2013/QH13 thì xử lý như sau:\", \"reason\": \"Tham chiếu trực tiếp đến quy định của Luật 45/2013/QH13\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XVI:16:section:2:2:article:255:4:clause:4:4"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:V:5:article:60:9:clause:3:3"})
MERGE (source)-[r:AP_DUNG_CHUYEN_TIEP]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"VERIFIED\", \"confidence\": 1.0, \"method\": \"RULE\", \"evidence_new\": \"khoản 3 Điều 60 của Luật Đất đai số 45/2013/QH13 thì được tiếp tục sử dụng đất trong thời hạn sử dụng đất còn lại mà không phải chuyển sang thuê đất theo quy định của Luật này.\", \"reason\": \"Tham chiếu trực tiếp đến quy định của Luật 45/2013/QH13\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XVI:16:section:2:2:article:255:4:clause:5:5"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:V:5:article:60:9:clause:4:4"})
MERGE (source)-[r:AP_DUNG_CHUYEN_TIEP]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"VERIFIED\", \"confidence\": 1.0, \"method\": \"RULE\", \"evidence_new\": \"khoản 4 Điều 60 của Luật Đất đai số 45/2013/QH13 thì được tiếp tục sử dụng đất trong thời hạn còn lại của dự án mà không phải chuyển sang thuê đất theo quy định của Luật này.\", \"reason\": \"Tham chiếu trực tiếp đến quy định của Luật 45/2013/QH13\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XVI:16:section:2:2:article:255:4:clause:6:6"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:V:5:article:60:9:clause:5:5"})
MERGE (source)-[r:AP_DUNG_CHUYEN_TIEP]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"VERIFIED\", \"confidence\": 1.0, \"method\": \"RULE\", \"evidence_new\": \"khoản 5 Điều 60 của Luật Đất đai số 45/2013/QH13 thì được lựa chọn tiếp tục thuê đất trong thời hạn sử dụng đất còn lại hoặc chuyển sang giao đất có thu tiền sử dụng đất theo quy định của Luật nà\", \"reason\": \"Tham chiếu trực tiếp đến quy định của Luật 45/2013/QH13\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XVI:16:section:2:2:article:260:9:clause:3:3"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:X:10:section:3:3:article:149:7:clause:5:5"})
MERGE (source)-[r:AP_DUNG_CHUYEN_TIEP]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"VERIFIED\", \"confidence\": 1.0, \"method\": \"RULE\", \"evidence_new\": \"khoản 5 Điều 149 của Luật Đất đai số 45/2013/QH13 thì được tiếp tục sử dụng đất theo thời hạn còn lại của dự án mà không phải chuyển sang thuê đất. Khi hết thời hạn thực hiện dự án nếu có nhu cầu \", \"reason\": \"Tham chiếu trực tiếp đến quy định của Luật 45/2013/QH13\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XVI:16:section:2:2:article:260:9:clause:6:6:point:d:4"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:X:10:section:3:3:article:151:9:clause:7:7"})
MERGE (source)-[r:AP_DUNG_CHUYEN_TIEP]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"VERIFIED\", \"confidence\": 1.0, \"method\": \"RULE\", \"evidence_new\": \"khoản 7 Điều 151 của Luật Đất đai số 45/2013/QH13 thì được tiếp tục sử dụng đất theo thời hạn còn lại của dự án mà không phải chuyển sang thuê đất. Khi hết thời hạn thực hiện dự án nếu có nhu cầu \", \"reason\": \"Tham chiếu trực tiếp đến quy định của Luật 45/2013/QH13\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XVI:16:section:2:2:article:252:1:clause:4:4"})
MATCH (target:LegalNode {id: "vbpl:32833"})
MERGE (source)-[r:LAM_HET_HIEU_LUC]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"VERIFIED\", \"confidence\": 1.0, \"method\": \"RULE\", \"evidence_new\": \"Luật Đất đai số 45/2013/QH13 ... hết hiệu lực kể từ ngày Luật này có hiệu lực thi hành.\", \"reason\": \"Khoản 4 Điều 252 quy định trực tiếp hiệu lực của Luật 45/2013/QH13\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:I:1:article:11:11"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:I:1:article:12:12"})
MERGE (source)-[r:TUONG_UNG]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"VERIFIED\", \"confidence\": 1.0, \"method\": \"RULE\", \"evidence_new\": \"Hành vi bị nghiêm cấm trong lĩnh vực đất đai\", \"evidence_old\": \"Những hành vi bị nghiêm cấm\", \"reason\": \"Hai Điều cùng quy định danh mục hành vi bị nghiêm cấm\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:I:1:article:2:2"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:I:1:article:2:2"})
MERGE (source)-[r:TUONG_UNG]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9653513431549072, \"evidence_new\": \"Điều 2. Đối tượng áp dụng\", \"evidence_old\": \"Điều 2. Đối tượng áp dụng\", \"reason\": \"Nội dung Điều 2 (2024) thể hiện Đối tượng áp dụng tương tự Nội dung Điều 2 (2013); cùng chức năng pháp lý.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:III:3:section:2:2:article:33:2"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:XI:11:section:2:2:article:174:2"})
MERGE (source)-[r:SUA_DOI]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9671599864959717, \"evidence_new\": \"Điều 33. Quyền và nghĩa vụ của tổ chức trong nước được Nhà nước giao đất có thu tiền sử dụng đất, cho thuê đất thu tiền thuê đất một lần cho cả thời gian thuê\", \"evidence_old\": \"Tổ chức kinh tế được Nhà nước giao đất có thu tiền sử dụng đất, cho thuê đất thu tiền thuê đất một lần cho cả thời gian thuê có quyền và nghĩa vụ chung quy định tại Điều 166 và Điều 170 của Luật này.\", \"reason\": \"Nội dung 2024 giữ nguyên chủ thể và quyền/nghĩa vụ cơ bản của tổ chức được Nhà nước giao đất có thu tiền sử dụng đất, cho thuê đất thu tiền thuê đất một lần cho cả thời gian thuê, nhưng bổ sung thêm các trường hợp và điều khoản mới (Khoản 2, 3, 4, 5) so với 2013.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:III:3:section:3:3:article:37:1"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:XI:11:section:3:3:article:179:1"})
MERGE (source)-[r:SUA_DOI]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9707508087158203, \"evidence_new\": \"Điểm a Quyền và nghĩa vụ chung quy định tại Điều 26 và Điều 31 của Luật này;\", \"evidence_old\": \"Điểm a Quyền và nghĩa vụ chung quy định tại Điều 166 và Điều 170 của Luật này;\", \"reason\": \"Nội dung chủ yếu về quyền và nghĩa vụ của cá nhân sử dụng đất với các hình thức nhận chuyển quyền, thừa kế, tặng cho, cho thuê, thế chấp, góp vốn được giữ lõi nhưng phạm vi và cách diễn đạt có đổi tên từ hộ gia đình sang cá nhân và thay đổi điều khoản tham chiếu.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:III:3:section:4:4:article:44:5"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:XI:11:section:4:4:article:186:5"})
MERGE (source)-[r:THAY_THE]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9893364906311035, \"evidence_new\": \"Điều 44. Quyền và nghĩa vụ về sử dụng đất ở của người gốc Việt Nam định cư ở nước ngoài được sở hữu nhà ở tại Việt Nam; người nước ngoài hoặc người gốc Việt Nam định cư ở nước ngoài không thuộc đối tượng được sở hữu nhà ở gắn liền với quyền sử dụng đất ở tại Việt Nam\", \"evidence_old\": \"Điều 186. Quyền và nghĩa vụ về sử dụng đất ở của người Việt Nam định cư ở nước ngoài được sở hữu nhà ở tại Việt Nam; người nước ngoài hoặc người Việt Nam định cư ở nước ngoài không thuộc đối tượng được mua nhà ở gắn liền với quyền sử dụng đất ở tại Việt Nam\", \"reason\": \"Nội dung Điều 44 giữ chủ đề quyền liên quan đến sở hữu nhà ở gắn với quyền sử dụng đất dành cho người Việt Nam định cư ở nước ngoài và điều chỉnh từ khía cạnh mua sang sở hữu, đồng thời bổ sung các hình thức chuyển nhượng/tặng cho/thừa kế và các trường hợp liên quan.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:IV:4:section:1:1:article:49:1"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:III:3:section:1:1:article:29:1"})
MERGE (source)-[r:THAY_THE]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9405875205993652, \"evidence_new\": \"Địa giới đơn vị hành chính được lập theo đơn vị hành chính cấp xã, cấp huyện, cấp tỉnh. Hồ sơ địa giới đơn vị hành chính thể hiện thông tin về việc thành lập, nhập, chia, điều chỉnh địa giới đơn vị hành chính và các mốc địa giới, đường địa giới của đơn vị hành chính đó.\", \"evidence_old\": \"Chính phủ chỉ đạo việc xác định địa giới hành chính, lập và quản lý hồ sơ địa giới hành chính các cấp trong phạm vi cả nước.\", \"reason\": \"Quy định mới về địa giới hành chính và hồ sơ địa giới được trình bày tại Khoản 1 Điều 49, mở rộng và sáp nhập nội dung liên quan, cho thấy thay thế toàn bộ nội dung của Điều 29.1.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:IV:4:section:1:1:article:49:1"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:III:3:section:2:2:article:31:1"})
MERGE (source)-[r:THAY_THE]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9018814563751221, \"evidence_new\": \"Địa giới đơn vị hành chính được lập theo đơn vị hành chính cấp xã, cấp huyện, cấp tỉnh. Hồ sơ địa giới đơn vị hành chính thể hiện thông tin về việc thành lập, nhập, chia, điều chỉnh địa giới đơn vị hành chính và các mốc địa giới, đường địa giới của đơn vị hành chính đó.\", \"evidence_old\": \"Việc đo đạc, lập bản đồ địa chính được thực hiện chi tiết đến từng thửa đất theo đơn vị hành chính xã, phường, thị trấn.\", \"reason\": \"Điều 31 về Lập, chỉnh lý bản đồ địa chính được thay thế bởi khung mới liên quan đến địa giới đơn vị hành chính và hồ sơ địa giới ở Điều 49, thể hiện thay thế nội dung của Điều 31:1.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:V:5:article:73:14"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:IV:4:article:46:12"})
MERGE (source)-[r:THAY_THE]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.92, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9527108669281006, \"evidence_new\": \"Điều 73. Rà soát, điều chỉnh quy hoạch, kế hoạch sử dụng đất\", \"evidence_old\": \"Việc điều chỉnh quy hoạch sử dụng đất chỉ được thực hiện trong các trường hợp sau đây:\", \"reason\": \"Quy định mới thay thế toàn bộ quy định cũ.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:VI:6:article:79:2"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:VI:6:section:1:1:article:62:2"})
MERGE (source)-[r:THAY_THE]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.92, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.907261848449707, \"evidence_new\": \"Khoản 32 Trường hợp thu hồi đất để thực hiện dự án, công trình vì lợi ích quốc gia, công cộng không thuộc các trường hợp quy định từ khoản 1 đến khoản 31 của Điều này thì Quốc hội sửa đổi, bổ sung các trường hợp thu hồi đất của Điều này theo trình tự, thủ tục rút gọn.\", \"evidence_old\": \"Điều 62. Thu hồi đất để phát triển kinh tế - xã hội vì lợi ích quốc gia, công cộng\", \"reason\": \"Điều 79 bao gồm cả Khoản 32 về việc Quốc hội sửa đổi, bổ sung các trường hợp thu hồi đất, cho thấy nội dung mới có cơ chế thay thế hoặc sửa đổi quy định cũ khi cần thiết, phản ánh vai trò thay thế của nội dung mới.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:VII:7:section:2:2:article:96:2"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:VI:6:section:2:2:article:77:4"})
MERGE (source)-[r:THAY_THE]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.88, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9649145603179932, \"evidence_new\": \"Điều 96. Bồi thường về đất khi Nhà nước thu hồi đất nông nghiệp của hộ gia đình, cá nhân\\n  Khoản 1\\n  Hộ gia đình, cá nhân đang sử dụng đất nông nghiệp khi Nhà nước thu hồi đất, nếu có đủ điều kiện được bồi thường quy định tại Điều 95 của Luật này thì được bồi thường bằng đất nông nghiệp hoặc bằng tiền hoặc bằng đất có mục đích sử dụng khác với loại đất thu hồi hoặc bằng nhà ở.\", \"evidence_old\": \"Điểm a\\n    Diện tích đất nông nghiệp được bồi thường bao gồm diện tích trong hạn mức theo quy định tại Điều 129, Điều 130 của Luật này và diện tích đất do được nhận thừa kế;\", \"reason\": \"Nội dung bồi thường về đất nông nghiệp tại Điều 96 gần như tương đồng với Điều 77:4 về nguyên tắc và phạm vi bồi thường (hạn mức, thừa kế, vượt hạn mức) và cập nhật tham chiếu pháp lý (176-177 thay cho 129-130; ngày 01/07/2014 thay cho ngày Luật có hiệu lực). Đây cho thấy quy định mới thay thế toàn bộ quy định cũ.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:VII:7:section:5:5:article:111:2"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:VI:6:section:2:2:article:86:13"})
MERGE (source)-[r:THAY_THE]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9276247024536133, \"evidence_new\": \"Điều 111. Bố trí tái định cư\", \"evidence_old\": \"thông báo cho người có đất ở thu hồi thuộc đối tượng phải di chuyển chỗ ở\", \"reason\": \"Điều 111 trong Luật Đất đai 2024 quy định về bố trí tái định cư với phạm vi, nội dung và cơ chế mới, được trình bày như một điều riêng (Điều 111), thay thế nội dung tái định cư trước đây ở Điều 86:13 của Luật Đất đai 2013.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:VIII:8:article:114:3"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:VIII:8:section:1:1:article:111:5"})
MERGE (source)-[r:SUA_DOI]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9181828498840332, \"evidence_new\": \"Quỹ phát triển đất của địa phương là quỹ tài chính nhà nước ngoài ngân sách do Ủy ban nhân dân cấp tỉnh thành lập để ứng vốn phục vụ các nhiệm vụ thuộc chức năng của tổ chức phát triển quỹ đất, thực hiện chính sách hỗ trợ đất đai đối với đồng bào dân tộc thiểu số và các nhiệm vụ khác theo quy định của pháp luật.\", \"evidence_old\": \"Quỹ phát triển đất của địa phương do Ủy ban nhân dân cấp tỉnh thành lập hoặc ủy thác cho Quỹ đầu tư phát triển, quỹ tài chính khác của địa phương để ứng vốn cho việc bồi thường, giải phóng mặt bằng và tạo quỹ đất theo quy hoạch, kế hoạch sử dụng đất đã được cơ quan nhà nước có thẩm quyền phê duyệt.\", \"reason\": \"Nội dung điều chỉnh mở rộng phạm vi và mục đích của Quỹ phát triển đất (bao gồm hỗ trợ đồng bào dân tộc thiểu số, thu hẹp mục tiêu lợi nhuận, bổ sung cơ chế hoàn vốn và yêu cầu chi tiết từ Chính phủ), đồng thời thay đổi cơ chế quản lý so với Điều 111/2013.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:VIII:8:article:115:4"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:VIII:8:section:1:1:article:111:5"})
MERGE (source)-[r:SUA_DOI]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.88, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.8823370933532715, \"evidence_new\": \"Tổ chức phát triển quỹ đất được thành lập để tạo lập, phát triển, quản lý, khai thác quỹ đất tại địa phương.\", \"evidence_old\": \"Quỹ phát triển đất của địa phương do Ủy ban nhân dân cấp tỉnh thành lập hoặc ủy thác cho Quỹ đầu tư phát triển, quỹ tài chính khác của địa phương để ứng vốn cho việc bồi thường, giải phóng mặt bằng và tạo quỹ đất theo quy hoạch, kế hoạch sử dụng đất đã được cơ quan nhà nước có thẩm quyền phê duyệt.\", \"reason\": \"Quy định mới về tổ chức phát triển quỹ đất kế thừa mục tiêu quản lý và phát triển quỹ đất địa phương, bổ sung hình thức thành lập tổ chức và cơ chế tài chính, thay thế nội dung Quỹ phát triển đất tại địa phương trong Luật cũ.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:IX:9:article:117:2"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:V:5:article:53:2"})
MERGE (source)-[r:SUA_DOI]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.95, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9462707042694092, \"evidence_new\": \"Việc quyết định giao đất, cho thuê đất đối với đất đang có người quản lý, sử dụng cho người khác chỉ được thực hiện sau khi cơ quan nhà nước có thẩm quyền quyết định thu hồi đất và phải thực hiện xong việc bồi thường, hỗ trợ, tái định cư theo quy định của pháp luật, trừ trường hợp được chuyển nhượng dự án bất động sản theo quy định của pháp luật về kinh doanh bất động sản.\", \"evidence_old\": \"Việc Nhà nước quyết định giao đất, cho thuê đất đối với đất đang có người sử dụng cho người khác chỉ được thực hiện sau khi cơ quan nhà nước có thẩm quyền quyết định thu hồi đất theo quy định của Luật này và phải thực hiện xong việc bồi thường, hỗ trợ, tái định cư theo quy định của pháp luật đối với trường hợp phải giải phóng mặt bằng.\", \"reason\": \"Nội dung chủ yếu về việc giao đất/cho thuê đất đối với đất đang có người sử dụng cho người khác sau khi thu hồi đất và bồi thường, hỗ trợ, tái định cư; Điều 117(2) bổ sung một ngoại lệ liên quan tới chuyển nhượng dự án bất động sản, do đó giữ lõi nhưng có thay đổi đáng kể.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:IX:9:article:121:6"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:V:5:article:57:6"})
MERGE (source)-[r:THAY_THE]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9758701324462891, \"evidence_new\": \"Điều 121. Chuyển mục đích sử dụng đất\", \"evidence_old\": \"Các trường hợp chuyển mục đích sử dụng đất phải được phép của cơ quan nhà nước có thẩm quyền bao gồm:\", \"reason\": \"Nội dung Điều 57 (2013) về chuyển mục đích sử dụng đất được thay thế bởi Điều 121 (2024) của Luật Đất đai 2024 với khung và danh mục điều kiện khác nhau, cho thấy thay thế toàn bộ khung pháp lý liên quan.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:IX:9:article:121:6"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:V:5:article:58:7"})
MERGE (source)-[r:THAY_THE]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9294474124908447, \"evidence_new\": \"Điều 121. Chuyển mục đích sử dụng đất\", \"evidence_old\": \"Điều kiện giao đất, cho thuê đất, cho phép chuyển mục đích sử dụng đất để thực hiện dự án đầu tư\", \"reason\": \"Điều 58 (2013) về điều kiện giao đất, cho thuê đất, cho phép chuyển mục đích sử dụng đất để thực hiện dự án đầu tư được xem xét lại và tổ chức lại trong khuôn khổ Luật Đất đai 2024, cho thấy sự thay đổi/điều chỉnh liên quan đến việc chuyển mục đích sử dụng đất.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:IX:9:article:121:6"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:V:5:article:59:8"})
MERGE (source)-[r:THAY_THE]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9248371124267578, \"evidence_new\": \"Điều 121. Chuyển mục đích sử dụng đất\", \"evidence_old\": \"Điều 59. Thẩm quyền giao đất, cho thuê đất, cho phép chuyển mục đích sử dụng đất\", \"reason\": \"Điều 59 (2013) thẩm quyền giao đất, cho thuê đất, cho phép chuyển mục đích sử dụng đất được quy định riêng; nội dung này chịu sự đổi mới trong Luật Đất đai 2024 với khung pháp lý mới cho chuyển mục đích sử dụng đất.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:IX:9:article:123:8"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:V:5:article:59:8"})
MERGE (source)-[r:SUA_DOI]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.88, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9683837890625, \"evidence_new\": \"Điểm a Giao đất, cho thuê đất, cho phép chuyển mục đích sử dụng đất đối với tổ chức trong nước;\", \"evidence_old\": \"Điểm a Giao đất, cho thuê đất, cho phép chuyển mục đích sử dụng đất đối với tổ chức;\", \"reason\": \"Nội dung thẩm quyền vẫn tương tự nhưng có bổ sung và sửa đổi đáng kể (thêm đối tượng và phạm vi áp dụng; bổ sung điều khoản cho cá nhân thuê đất nông nghiệp với yêu cầu văn bản chấp thuận, bổ sung tính năng xã, bổ sung điều khoản không được phân cấp/ủy quyền; có thêm khoản 5).\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:X:10:section:3:3:article:152:19"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:VII:7:section:2:2:article:106:10"})
MERGE (source)-[r:THAY_THE]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9264130592346191, \"evidence_new\": \"Điều 152. Đính chính, thu hồi, hủy giấy chứng nhận đã cấp\", \"evidence_old\": \"Điều 106. Đính chính, thu hồi Giấy chứng nhận đã cấp\", \"reason\": \"Nội dung và chức năng về đính chính và thu hồi giấy chứng nhận đã cấp được tái xuất hiện và mở rộng ở Điều 152/2024, cho thấy quy định mới thay thế toàn bộ quy định cũ.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XI:11:section:1:1:article:156:4"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:VIII:8:section:1:1:article:109:3"})
MERGE (source)-[r:SUA_DOI]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9633617401123047, \"evidence_new\": \"Điều 156. Nộp tiền sử dụng đất, tiền thuê đất khi chuyển mục đích sử dụng đất, gia hạn sử dụng đất, điều chỉnh thời hạn sử dụng đất\", \"evidence_old\": \"Điều 109. Nộp tiền sử dụng đất, tiền thuê đất khi chuyển mục đích sử dụng đất, gia hạn sử dụng đất\", \"reason\": \"Nội dung lõi liên quan tới nộp tiền sử dụng đất, tiền thuê đất khi chuyển mục đích sử dụng đất và gia hạn, được duy trì ở văn bản mới với chỉnh sửa nhỏ về tham chiếu và bổ sung.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XIII:13:section:2:2:article:176:1"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:X:10:section:2:2:article:129:1"})
MERGE (source)-[r:THAY_THE]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.92, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9730424880981445, \"evidence_new\": \"Hạn mức giao đất trồng cây hằng năm, đất nuôi trồng thủy sản, đất làm muối cho cá nhân trực tiếp sản xuất nông nghiệp được quy định như sau:\", \"evidence_old\": \"Hạn mức giao đất trồng cây hàng năm, đất nuôi trồng thủy sản, đất làm muối cho mỗi hộ gia đình, cá nhân trực tiếp sản xuất nông nghiệp như sau:\", \"reason\": \"Nội dung chính về hạn mức giao đất nông nghiệp được quy định lại trong Điều 176 (2024), thay thế toàn bộ quy định cũ tại Điều 129 (2013).\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XIII:13:section:2:2:article:179:4"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:X:10:section:2:2:article:132:4"})
MERGE (source)-[r:SUA_DOI]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.92, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9543795585632324, \"evidence_new\": \"Quỹ đất nông nghiệp sử dụng vào mục đích công ích của xã, phường, thị trấn do Ủy ban nhân dân cấp xã nơi có đất quản lý, sử dụng theo quy hoạch, kế hoạch sử dụng đất đã được cơ quan có thẩm quyền phê duyệt.\", \"evidence_old\": \"Quỹ đất nông nghiệp sử dụng vào mục đích công ích của xã, phường, thị trấn do Ủy ban nhân dân cấp xã nơi có đất quản lý, sử dụng theo quy hoạch, kế hoạch sử dụng đất đã được cơ quan nhà nước có thẩm quyền phê duyệt.\", \"reason\": \"Nội dung Điều 179.4 có cùng chủ đề và vẫn điều chỉnh quỹ đất nông nghiệp sử dụng vào mục đích công ích so với Điều 132.4 trước đây; khác biệt ngôn ngữ và căn cứ phê duyệt.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XIII:13:section:2:2:article:205:30"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:X:10:section:3:3:article:152:10"})
MERGE (source)-[r:SUA_DOI]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.9, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9459269046783447, \"evidence_new\": \"Đất sử dụng cho hoạt động khoáng sản bao gồm đất để thăm dò, khai thác khoáng sản và khu vực các công trình phụ trợ cho hoạt động khoáng sản.\", \"evidence_old\": \"Đất sử dụng cho hoạt động khoáng sản bao gồm đất để thăm dò, khai thác, chế biến khoáng sản và khu vực các công trình phụ trợ cho hoạt động khoáng sản và hành lang an toàn trong hoạt động khoáng sản.\", \"reason\": \"Nội dung lõi về sử dụng đất cho hoạt động khoáng sản được giữ và có sửa đổi, bổ sung so với Điều 152; quy định mới bổ sung và bổ sung nội dung đáng kể (ví dụ bổ sung điều về an ninh trật tự và quản lý quỹ đất).\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XIII:13:section:2:2:article:206:31"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:X:10:section:3:3:article:153:11"})
MERGE (source)-[r:SUA_DOI]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.95, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9717774391174316, \"evidence_new\": \"Đất thương mại, dịch vụ bao gồm đất xây dựng cơ sở kinh doanh thương mại, dịch vụ và các công trình khác phục vụ cho kinh doanh, thương mại, dịch vụ.\", \"evidence_old\": \"Đất thương mại, dịch vụ bao gồm đất xây dựng cơ sở kinh doanh thương mại, dịch vụ và các công trình khác phục vụ cho kinh doanh, thương mại, dịch vụ.\", \"reason\": \"Nội dung lõi về đất thương mại, dịch vụ và đất cơ sở sản xuất phi nông nghiệp được giữ, nhưng Điều 206 bổ sung thêm phạm vi áp dụng, đối tượng và quy định liên quan đến người Việt Nam định cư ở nước ngoài và cơ chế th thuê/nhận góp vốn bằng quyền sử dụng đất, thể hiện sự sửa đổi đáng kể so với Điều 153:11.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XIII:13:section:2:2:article:211:36"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:X:10:section:3:3:article:158:16"})
MERGE (source)-[r:THAY_THE]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.946824312210083, \"evidence_new\": \"Đất có di tích lịch sử - văn hóa, danh lam thắng cảnh, di sản thiên nhiên đã được xếp hạng hoặc được Ủy ban nhân dân cấp tỉnh đưa vào danh mục kiểm kê di tích theo quy định của pháp luật về di sản văn hóa thì phải được quản lý theo quy định sau đây:\", \"evidence_old\": \"Đất có di tích lịch sử - văn hóa, danh lam thắng cảnh đã được xếp hạng hoặc được Ủy ban nhân dân cấp tỉnh quyết định bảo vệ thì phải được quản lý nghiêm ngặt theo quy định sau đây:\", \"reason\": \"Nội dung Điều 211 về đất có di tích lịch sử - văn hóa có phạm vi quản lý, quyền và trách nhiệm tương đồng với Điều 158 và bổ sung, mở rộng (ví dụ quy định về chuyển mục đích sử dụng, khu vực bảo vệ và bồi thường), cho thấy quy định mới có thể thay thế toàn bộ quy định cũ.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XIII:13:section:2:2:article:213:38"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:X:10:section:3:3:article:159:17"})
MERGE (source)-[r:SUA_DOI]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9120082855224609, \"evidence_new\": \"Đất tôn giáo bao gồm đất xây dựng cơ sở tôn giáo, trụ sở của tổ chức tôn giáo, tổ chức tôn giáo trực thuộc và công trình tôn giáo hợp pháp khác.\", \"evidence_old\": \"Đất cơ sở tôn giáo gồm đất thuộc chùa, nhà thờ, nhà nguyện, thánh thất, thánh đường, niệm phật đường, tu viện, trường đào tạo riêng của tôn giáo, trụ sở của tổ chức tôn giáo, các cơ sở khác của tôn giáo được Nhà nước cho phép hoạt động.\", \"reason\": \"Nội dung mới định nghĩa lại đất tôn giáo/đất cơ sở tôn giáo, mở rộng phạm vi và bổ sung cách thức giao đất; so với Điều 159 năm 2013, nội dung lõi liên quan đến đất cho cơ sở tôn giáo được giữ nhưng có bổ sung và điều chỉnh đáng kể.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XIII:13:section:2:2:article:215:40"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:X:10:section:3:3:article:163:21"})
MERGE (source)-[r:SUA_DOI]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.92, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9567005634307861, \"evidence_new\": \"Điểm a Nhà nước giao cho tổ chức để quản lý kết hợp sử dụng, khai thác đất có mặt nước chuyên dùng vào mục đích phi nông nghiệp hoặc phi nông nghiệp kết hợp với nuôi trồng, khai thác thủy sản;\", \"evidence_old\": \"Điểm a Nhà nước giao cho tổ chức để quản lý kết hợp sử dụng, khai thác đất có mặt nước chuyên dùng vào mục đích phi nông nghiệp hoặc phi nông nghiệp kết hợp với nuôi trồng và khai thác thủy sản;\", \"reason\": \"Nội dung về quản lý và sử dụng đất sông, ngòi, kênh, rạch, suối và mặt nước chuyên dụng được giữ, nhưng điều chỉnh phạm vi đối tượng và bổ sung nội dung thêm (phạm vi bảo vệ, điều kiện cấp phép) so vớiĐiểm a–c của Điều 163:21, cho thấy sửa đổi có yếu tố bổ sung đáng kể mà không thay thế toàn bộ nội dung cũ.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XIV:14:article:226:4"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:XII:12:article:197:3"})
MERGE (source)-[r:SUA_DOI]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.86, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.953925371170044, \"evidence_new\": \"Cơ quan có thẩm quyền giải quyết thủ tục hành chính về đất đai phải thực hiện đúng trình tự, thủ tục theo quy định và công khai kết quả giải quyết thủ tục hành chính.\", \"evidence_old\": \"Cơ quan có thẩm quyền giải quyết thủ tục hành chính về đất đai phải thực hiện đúng trình tự, thủ tục theo quy định.\", \"reason\": \"Quy định mới bổ sung nội dung công khai kết quả giải quyết thủ tục hành chính vào Khoản 3 so với Khoản 3 của Điều 197.3, làm rõ thêm nghĩa vụ công khai kết quả giải quyết thủ tục hành chính.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XV:15:section:2:2:article:236:3"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:XIII:13:section:2:2:article:203:3"})
MERGE (source)-[r:SUA_DOI]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9412286281585693, \"evidence_new\": \"Điều 236. Thẩm quyền giải quyết tranh chấp đất đai\", \"evidence_old\": \"Điều 203. Thẩm quyền giải quyết tranh chấp đất đai\", \"reason\": \"Nội dung chính về thẩm quyền giải quyết tranh chấp đất đai được duy trì, nhưng quy định được bố trí lại thành Điều 236 với bổ sung và mở rộng các cơ chế xử lý; cụ thể có sự xác định rõ về thẩm quyền và các hình thức giải quyết tranh chấp, khác so với Điều 203:3 của Luật Đất đai 2013.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XV:15:section:2:2:article:238:5"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:XIII:13:section:2:2:article:205:5"})
MERGE (source)-[r:SUA_DOI]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9447720050811768, \"evidence_new\": \"Việc thu thập, bảo quản, sử dụng và lưu trữ hồ sơ, tài liệu liên quan đến giải quyết tố cáo về quản lý, sử dụng đất đai thực hiện theo quy định của pháp luật về tố cáo.\", \"evidence_old\": \"Việc giải quyết tố cáo vi phạm pháp luật về quản lý và sử dụng đất đai thực hiện theo quy định của pháp luật về tố cáo.\", \"reason\": \"Nội dung Khoản 1-2 tương đồng với Khoản 1-2 của Điều 238; Khoản 3 của Điều 238 bổ sung nội dung lưu trữ hồ sơ.\"}");

MATCH (source:LegalNode {id: "vbpl:177815:chapter:XVI:16:section:2:2:article:252:1"})
MATCH (target:LegalNode {id: "vbpl:32833:chapter:XIV:14:article:211:2"})
MERGE (source)-[r:THAY_THE]->(target)
SET r += apoc.convert.fromJsonMap("{\"status\": \"PROPOSED\", \"confidence\": 0.85, \"method\": \"LLM\", \"model\": \"gpt-5-nano\", \"similarity_score\": 0.9260406494140625, \"evidence_new\": \"Khoản 4 Luật Đất đai số 45/2013/QH13 đã được sửa đổi, bổ sung một số điều theo Luật số 35/2018/QH14 (sau đây gọi là Luật Đất đai số 45/2013/QH13) hết hiệu lực kể từ ngày Luật này có hiệu lực thi hành.\", \"evidence_old\": \"Khoản 1 Luật này có hiệu lực thi hành từ ngày 01 tháng 7 năm 2014.\", \"reason\": \"Nội dung điều 211.2 về hiệu lực thi hành và các quy định cũ được thay thế bởi quy định tại Điều 252 của Luật Đất đai 2024, thể hiện việc Luật Đất đai 45/2013/QH13 hết hiệu lực từ khi Luật mới có hiệu lực thi hành.\"}");
