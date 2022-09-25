
aaaa
WITH
    database1.tableFromWith AS (SELECT aa.* FROM table3 as aa 
                                left join table4 on aa.col1=table4.col2),
    test as (SELECT * from table3)
SELECT
  "xxxxx"
FROM
  database1.tableFromWith alias
LEFT JOIN database2.table2 ON ("tt"."ttt"."fff" = "xx"."xxx");


INSERT /* VoteHelper::addVote xxx */  INTO `page_vote` (article_id,user_id,`time`) 
SELECT * FROM table2;
